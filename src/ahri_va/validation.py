"""Lossless linkage and sequential adult/target eligibility; no model fitting."""

from collections import Counter
from collections.abc import Iterable, Iterator
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from importlib.resources import files
import json
from pathlib import Path
import re
from typing import TypedDict

from ahri_va.config import Configuration, ValidationError


__all__ = ["EligibleInputs", "PREDICTORS", "validate_inputs"]

# A fixed documentary allowlist, never inferred from input column prefixes.
PREDICTORS: tuple[str, ...] = tuple(json.loads(
    files("ahri_va").joinpath("predictors.json").read_text(encoding="utf-8")
))
_DEATH_FIELDS = ("Age_in_years", "cause1_InterVA")
_AGE_NUMBER = re.compile(r"[+]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class InputCounts(TypedDict):
    rows: int
    missing_identifiers: int
    unmatched: int


class EligibilitySummary(TypedDict):
    status: str
    scope: str
    benchmark_feasibility: str
    models_fitted: int
    inputs: dict[str, InputCounts]
    matched_records: int
    exclusions: dict[str, int]
    eligible_labelled_adults: int
    distinct_target_classes: int
    undetermined_assignments: int
    predictor_count: int
    eligible_indicator_states: dict[str, int]


@dataclass(frozen=True)
class EligibleInputs:
    """Eligible feature rows and exact labels, plus a value-free command summary.

    Features follow PREDICTORS order, contain only y/n/-, and correspond to
    targets in deaths-file order. Identifiers and metadata are not features.
    Records stay in memory; summary contains aggregate counts only.
    """

    features: tuple[tuple[str, ...], ...]
    targets: tuple[str, ...]
    summary: EligibilitySummary


@dataclass
class _Table:
    records: dict[str, tuple[str, ...]]
    rows: int
    missing_identifiers: int


def _check_header(header: list[str], required: tuple[str, ...], role: str) -> None:
    if not header:
        raise ValidationError(f"{role}: missing CSV header; required fields must be in record one.")
    if header[0].startswith("\ufeff"):
        raise ValidationError(f"{role}: a byte-order mark precedes the header; use UTF-8 without BOM.")
    blank = sum(not field.strip() for field in header)
    duplicates = len(header) - len(set(header))
    if blank or duplicates:
        raise ValidationError(
            f"{role}: invalid header; blank_fields={blank}; duplicate_fields={duplicates}."
        )
    missing = [field for field in required if field not in header]
    if missing:
        raise ValidationError(
            f"{role}: missing_required_fields={len(missing)}: {', '.join(missing)}."
        )


def _strict_lines(stream: Iterable[str]) -> Iterator[str]:
    # csv.reader(strict=True) still accepts quotes inside unquoted fields.
    # Enforce the declared quoting grammar before passing text to the reader.
    state = "start"
    for line in stream:
        for character in line:
            if state == "quoted":
                if character == '"':
                    state = "closed"
            elif state == "closed":
                if character == '"':
                    state = "quoted"
                elif character in ",\r\n":
                    state = "start"
                else:
                    raise csv.Error("Unexpected text after a closing quote.")
            elif character in ",\r\n":
                state = "start"
            elif character == '"':
                if state != "start":
                    raise csv.Error("Quote inside an unquoted field.")
                state = "quoted"
            else:
                state = "unquoted"
        yield line


def _read_table(path: Path, role: str, config: Configuration) -> _Table:
    fields = PREDICTORS if role == "indicators" else _DEATH_FIELDS
    identifiers: Counter[str] = Counter()
    invalid_indicators: Counter[str] = Counter()
    conflicts: set[str] = set()
    records: dict[str, tuple[str, ...]] = {}
    rows = missing_identifiers = invalid_identifiers = malformed = 0
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(_strict_lines(stream), delimiter=",", quotechar='"', doublequote=True,
                                escapechar=None, strict=True)
            header = next(reader, [])
            _check_header(header, ("IIntID", *fields), role)
            key_index = header.index("IIntID")
            indices = [header.index(field) for field in fields]
            for cells in reader:
                rows += 1
                if len(cells) != len(header):
                    malformed += 1
                    continue
                selected = tuple(cells[index] for index in indices)
                if role == "indicators":
                    if config.map_indicator_blanks:
                        selected = tuple("-" if value == "" else value for value in selected)
                    for field, value in zip(fields, selected):
                        if value not in ("y", "n", "-"):
                            invalid_indicators[field] += 1
                identifier = cells[key_index]
                if identifier in config.identifier_missing:
                    missing_identifiers += 1
                    continue
                if not identifier.strip() or _CONTROL.search(identifier):
                    invalid_identifiers += 1
                    continue
                identifiers[identifier] += 1
                if identifier in records:
                    if role == "deaths" and records[identifier][1] != selected[1]:
                        conflicts.add(identifier)
                else:
                    records[identifier] = selected
    except (csv.Error, UnicodeError):
        raise ValidationError(
            f"{role}: malformed_records_detected=1; check UTF-8 encoding, CSV quoting "
            "and field lengths (maximum 131072 characters per field)."
        ) from None
    except OSError:
        raise ValidationError(f"{role}: cannot read input; check the supplied file and permissions.") from None
    errors = []
    if malformed:
        errors.append(f"{role}: malformed_records={malformed}; field count differs from header.")
    if invalid_identifiers:
        errors.append(
            f"{role}.IIntID: unusable_identifiers={invalid_identifiers}; "
            "undeclared whitespace-only or control-character keys are not usable."
        )
    duplicates = sum(count > 1 for count in identifiers.values())
    if duplicates:
        duplicate_rows = sum(count for count in identifiers.values() if count > 1)
        errors.append(
            f"{role}.IIntID: duplicate_identifier_groups={duplicates}; "
            f"duplicate_identifier_rows={duplicate_rows}; require unique identifiers."
        )
    if conflicts:
        errors.append(f"deaths.cause1_InterVA: conflicting_target_identifiers={len(conflicts)}.")
    for field, count in invalid_indicators.items():
        errors.append(
            f"indicators.{field}: undeclared_values={count}; require y, n or -; "
            "blank cells require an explicitly reviewed missing/inapplicable mapping."
        )
    if errors:
        raise ValidationError("\n".join(errors))
    return _Table(records, rows, missing_identifiers)


def _age_exclusion(value: str, config: Configuration) -> str | None:
    if value in config.age_missing:
        return "missing_age"
    # No float rounding, implicit trimming, separators, NaN or infinity.
    if not _AGE_NUMBER.fullmatch(value):
        return "invalid_age"
    try:
        age = Decimal(value)
        if not age.is_finite() or age != age.to_integral_value():
            return "invalid_age"
        return "under_18" if age < 18 else None
    except InvalidOperation:
        return "invalid_age"


def validate_inputs(deaths: Path, indicators: Path, config: Configuration) -> EligibleInputs:
    """Validate both tables and construct eligible labelled adults in memory.

    Args:
        deaths: UTF-8 CSV with IIntID, Age_in_years and cause1_InterVA.
        indicators: UTF-8 CSV with IIntID and all 353 allowlisted indicators.
        config: Explicit settings returned by load_configuration.

    Returns:
        Exact feature categories and target labels with reconcilable aggregate
        counts. Zero eligible records is a valid input/eligibility outcome;
        class and partition feasibility are not established by this milestone.

    Raises:
        ValidationError: Malformed input, absent required columns, invalid
            indicators or ambiguous keys. Diagnostics omit record values.
    """
    death_table = _read_table(deaths, "deaths", config)
    indicator_table = _read_table(indicators, "indicators", config)
    matched = death_table.records.keys() & indicator_table.records.keys()
    exclusions = dict.fromkeys(
        ("missing_age", "invalid_age", "under_18", "missing_target", "unusable_target"), 0,
    )
    features = []
    targets = []
    states: Counter[str] = Counter()
    for identifier, (age, target) in death_table.records.items():
        if identifier not in matched:
            continue
        reason = _age_exclusion(age, config)
        if reason is None:
            if target in config.target_missing:
                reason = "missing_target"
            elif not target.strip() or _CONTROL.search(target):
                reason = "unusable_target"
        if reason is not None:
            exclusions[reason] += 1
            continue
        row = indicator_table.records[identifier]
        features.append(row)
        targets.append(target)
        states.update(row)
    summary: EligibilitySummary = {
        "status": "valid",
        "scope": "input_integrity_and_adult_label_eligibility",
        "benchmark_feasibility": "not_checked",
        "models_fitted": 0,
        "inputs": {
            "deaths": {"rows": death_table.rows,
                       "missing_identifiers": death_table.missing_identifiers,
                       "unmatched": len(death_table.records) - len(matched)},
            "indicators": {"rows": indicator_table.rows,
                           "missing_identifiers": indicator_table.missing_identifiers,
                           "unmatched": len(indicator_table.records) - len(matched)},
        },
        "matched_records": len(matched),
        "exclusions": exclusions,
        "eligible_labelled_adults": len(targets),
        "distinct_target_classes": len(set(targets)),
        "undetermined_assignments": targets.count(config.undetermined_label),
        "predictor_count": len(PREDICTORS),
        "eligible_indicator_states": {state: states[state] for state in ("y", "n", "-")},
    }
    return EligibleInputs(tuple(features), tuple(targets), summary)
