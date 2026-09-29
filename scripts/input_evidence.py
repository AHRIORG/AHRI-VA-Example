#!/usr/bin/env python3
"""Private input evidence commands. Development uses invented records exclusively."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import zlib
from typing import Any, Literal


SCHEMA = json.loads(Path(__file__).with_name("documented-schema.json").read_text())
REVIEW_TOPICS = (
    "v2_compatibility", "identifier_preservation", "age_at_death",
    "missing_conventions", "undetermined_assignment", "preparation",
)
REVIEW_STATUSES = ("unresolved", "documentary_only", "user_confirmed")
DELIMITERS = {"comma": ",", "semicolon": ";", "tab": "\t", "pipe": "|"}
QUOTES = {"double": '"', "single": "'", "none": None}
ENCODINGS = ("utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1")
COUNT_FIELDS = (
    "rows", "blank_identifiers", "blank_targets", "blank_ages",
    "declared_missing_identifiers", "declared_missing_targets", "declared_missing_ages",
    "leading_zero_identifiers", "large_digit_identifiers", "whitespace_identifiers",
    "decimal_or_exponent_identifiers", "non_completed_year_number_ages",
    "duplicate_identifier_groups", "duplicate_identifier_rows", "conflicting_target_identifiers",
    "indicator_y", "indicator_n", "indicator_missing_inapplicable", "indicator_blank", "indicator_unexpected",
)
RELEASE_SECTIONS = ("inventory", "serialization", "schema", "characteristics")
ROLES = ("deaths", "indicators", "other", "unknown")
FORMATS = ("delimited", "xlsx", "stata", "spss", "sas", "parquet", "json", "other", "unknown")
ORGANISATIONS = ("single_table", "multiple_tables", "multiple_sheets", "unknown")
CONTAINERS = ("no_recognized_container", "gzip", "zip", "bzip2", "xz", "zstd")
INDICATOR_CATEGORIES = {"y": "y", "n": "n", "-": "missing_inapplicable", "": "blank"}


class EvidenceError(Exception):
    """A fixed, value-free diagnostic suitable for the command boundary."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceError("Expected a JSON object; consult the private-execution guide.")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def initialize(work: Path) -> None:
    work.mkdir(mode=0o700)  # A new directory prevents overwriting earlier evidence.
    write_json(work / "inventory.json", {
        "files": [],
        "missing_tokens": {"identifier": None, "age": None, "target": None},
        "indicator_blank_mapping": "unresolved",
    })
    review: dict[str, Any] = {
        topic: {"status": "unresolved", "private_evidence": "",
                "release_statement": "", "release_approved": False}
        for topic in REVIEW_TOPICS
    }
    review["release_sections"] = dict.fromkeys(RELEASE_SECTIONS, False)
    write_json(work / "review.json", review)


def config_digest(config: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def inventory_config(work: Path) -> dict[str, Any]:
    config = read_json(work / "inventory.json")
    files = config.get("files")
    if not isinstance(files, list) or not files:
        raise EvidenceError("Inventory must list at least one input; no native format is assumed.")
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise EvidenceError("Each inventory input needs a private path.")
        if not Path(entry["path"]).is_absolute():
            raise EvidenceError("Input paths must be absolute and remain in the analysis account.")
        if entry.get("role") not in ROLES:
            raise EvidenceError("Choose deaths, indicators, other or unknown for each input role.")
        if entry.get("format") not in FORMATS:
            raise EvidenceError("Choose a documented inventory format option.")
        if entry.get("table_organisation") not in ORGANISATIONS:
            raise EvidenceError("Choose a documented table organisation option.")
    tokens = config.get("missing_tokens")
    if not isinstance(tokens, dict):
        raise EvidenceError("Declare missing_tokens, keeping unverified conventions null.")
    for field in ("identifier", "age", "target"):
        value = tokens.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(v, str) for v in value)):
            raise EvidenceError("Missing tokens must be null or a list of exact strings.")
    if config.get("indicator_blank_mapping") not in ("unresolved", "reject", "missing_inapplicable"):
        raise EvidenceError("Choose unresolved, reject or missing_inapplicable for indicator blanks.")
    return config


def parsing_config(entry: dict[str, Any]) -> dict[str, Any]:
    parsing = entry.get("serialization")
    if not isinstance(parsing, dict):
        raise EvidenceError("Delimited inspection requires explicit serialization settings.")
    if (parsing.get("encoding") not in ENCODINGS
            or parsing.get("delimiter") not in DELIMITERS
            or parsing.get("quote") not in QUOTES
            or parsing.get("escape") not in ("none", "backslash")
            or type(parsing.get("doublequote")) is not bool
            or type(parsing.get("header_row")) is not int
            or parsing["header_row"] < 1):
        raise EvidenceError("Invalid serialization settings; use the options in the guide.")
    return {key: parsing[key] for key in (
        "encoding", "delimiter", "quote", "escape", "doublequote", "header_row",
    )}


@dataclass
class InspectedTable:
    evidence: dict[str, Any]
    identifiers: Counter[str]


def inspect_delimited(entry: dict[str, Any], config: dict[str, Any], container: str) -> InspectedTable:
    parsing = parsing_config(entry)
    role = entry["role"]
    expected = SCHEMA.get(role, [])
    required = (["IIntID", "Age_in_years", "cause1_InterVA"] if role == "deaths"
                else ["IIntID", *SCHEMA["predictors"]] if role == "indicators" else [])
    identifiers: Counter[str] = Counter()
    targets: dict[str, str] = {}
    conflicts: set[str] = set()
    counts: dict[str, Any] = {name: 0 for name in (
        "rows", "blank_identifiers", "blank_targets", "blank_ages",
        "leading_zero_identifiers", "large_digit_identifiers", "whitespace_identifiers",
        "decimal_or_exponent_identifiers", "non_completed_year_number_ages",
        "indicator_y", "indicator_n", "indicator_missing_inapplicable", "indicator_blank",
        "indicator_unexpected",
    )}
    tokens = config["missing_tokens"]
    for field in ("identifier", "age", "target"):
        counts[f"declared_missing_{field}s"] = 0 if tokens[field] is not None else None
    opener = gzip.open if container == "gzip" else open
    with opener(entry["path"], mode="rt", encoding=parsing["encoding"], newline="") as stream:
        reader = csv.reader(
            stream, delimiter=DELIMITERS[parsing["delimiter"]],
            quotechar=QUOTES[parsing["quote"]],
            quoting=csv.QUOTE_NONE if parsing["quote"] == "none" else csv.QUOTE_MINIMAL,
            escapechar="\\" if parsing["escape"] == "backslash" else None,
            doublequote=parsing["doublequote"], strict=True,
        )
        for _ in range(parsing["header_row"] - 1):
            next(reader)
        header = next(reader)
        if not header or len(set(header)) != len(header) or any(not h for h in header):
            raise EvidenceError("Header is empty or contains blank/duplicate fields.")
        for cells in reader:
            if len(cells) != len(header):
                raise EvidenceError("Malformed delimited record: field count differs from header.")
            row = dict(zip(header, cells))
            counts["rows"] += 1
            identifier = row.get("IIntID", "")
            counts["blank_identifiers"] += identifier == ""
            counts["whitespace_identifiers"] += identifier != identifier.strip()
            digits = bool(re.fullmatch(r"[0-9]+", identifier))
            counts["leading_zero_identifiers"] += digits and len(identifier) > 1 and identifier[0] == "0"
            significant = identifier.lstrip("0")
            counts["large_digit_identifiers"] += digits and (len(significant) > 16 or (
                len(significant) == 16 and significant > "9007199254740991"))
            counts["decimal_or_exponent_identifiers"] += bool(re.fullmatch(
                r"[+-]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+|[0-9]+[eE][+-]?[0-9]+)", identifier))
            if tokens["identifier"] is not None:
                counts["declared_missing_identifiers"] += identifier in tokens["identifier"]
            if identifier and identifier not in (tokens["identifier"] or []):
                identifiers[identifier] += 1
                if "cause1_InterVA" in row:
                    target = row["cause1_InterVA"]
                    if identifier in targets and targets[identifier] != target:
                        conflicts.add(identifier)
                    targets[identifier] = target
            if "cause1_InterVA" in row:
                target = row["cause1_InterVA"]
                counts["blank_targets"] += target == ""
                if tokens["target"] is not None:
                    counts["declared_missing_targets"] += target in tokens["target"]
            if "Age_in_years" in row:
                age = row["Age_in_years"]
                counts["blank_ages"] += age == ""
                if tokens["age"] is not None:
                    counts["declared_missing_ages"] += age in tokens["age"]
                if age and age not in (tokens["age"] or []):
                    try:
                        number = Decimal(age)
                        valid = number.is_finite() and number >= 0 and number == number.to_integral_value()
                    except InvalidOperation:
                        valid = False
                    counts["non_completed_year_number_ages"] += not valid
            if role == "indicators":
                for field in SCHEMA["predictors"]:
                    if field in row:
                        category = INDICATOR_CATEGORIES.get(row[field], "unexpected")
                        counts[f"indicator_{category}"] += 1
    counts["duplicate_identifier_groups"] = sum(count > 1 for count in identifiers.values())
    counts["duplicate_identifier_rows"] = sum(count for count in identifiers.values() if count > 1)
    counts["conflicting_target_identifiers"] = len(conflicts)
    if role != "indicators":
        for name in COUNT_FIELDS:
            if name.startswith("indicator_"):
                counts[name] = None
    # An absent field is not evidence of zero missing values.
    for field, names in {
        "IIntID": ("blank_identifiers", "declared_missing_identifiers", "duplicate_identifier_groups",
                    "duplicate_identifier_rows", "leading_zero_identifiers", "large_digit_identifiers",
                    "whitespace_identifiers", "decimal_or_exponent_identifiers", "conflicting_target_identifiers"),
        "Age_in_years": ("blank_ages", "declared_missing_ages", "non_completed_year_number_ages"),
        "cause1_InterVA": ("blank_targets", "declared_missing_targets", "conflicting_target_identifiers"),
    }.items():
        if field not in header:
            for name in names:
                counts[name] = None
    return InspectedTable({
        "status": "observed", "parsing": parsing,
        "schema": {
            "expected_fields": len(expected), "observed_fields": len(header),
            "missing_documented_fields": [field for field in expected if field not in header],
            "missing_required_fields": [field for field in required if field not in header],
            "extra_field_count": len(set(header) - set(expected)),
            "predictors_present": len(set(header) & set(SCHEMA["predictors"])),
        }, "counts": counts,
    }, identifiers)


def inventory_entry(entry: dict[str, Any], index: int) -> dict[str, Any]:
    with Path(entry["path"]).open("rb") as stream:
        signature = stream.read(8)
    container = "no_recognized_container"
    for magic, name in ((b"\x1f\x8b", "gzip"), (b"PK", "zip"), (b"BZh", "bzip2"),
                        (b"\xfd7zXZ\x00", "xz"), (b"\x28\xb5\x2f\xfd", "zstd")):
        if signature.startswith(magic):
            container = name
            break
    return {"input": index, "role": entry["role"], "declared_format": entry["format"],
            "declared_organisation": entry["table_organisation"], "observed_container": container}


def inspect_inputs(work: Path, inventory_only: bool = False) -> None:
    (work / "candidate-summary.md").unlink(missing_ok=True)
    config = inventory_config(work)
    tables = []
    for index, entry in enumerate(config["files"], 1):
        try:
            info = inventory_entry(entry, index)
            if inventory_only:
                table = InspectedTable({"status": "inventoried"}, Counter())
            elif (entry["format"] != "delimited" or entry["role"] not in ("deaths", "indicators")
                  or info["observed_container"] not in ("gzip", "no_recognized_container")):
                table = InspectedTable({"status": "unsupported"}, Counter())
            elif entry.get("serialization") is None:
                table = InspectedTable({"status": "serialization_unresolved"}, Counter())
            else:
                table = inspect_delimited(entry, config, info["observed_container"])
            table.evidence.update(info)
        except (OSError, UnicodeError, csv.Error, StopIteration, EvidenceError, EOFError, zlib.error):
            # Parser exceptions may embed paths or cell values. Never serialize them.
            table = InspectedTable({"input": index, "role": entry["role"],
                                    "declared_format": entry["format"], "status": "unreadable_or_malformed"}, Counter())
        tables.append(table)
    deaths = [t for t in tables if t.evidence["role"] == "deaths"]
    indicators = [t for t in tables if t.evidence["role"] == "indicators"]
    linkage: dict[str, Any] = {"status": "unresolved"}
    if (len(deaths) == len(indicators) == 1 and all(
            t.evidence["status"] == "observed"
            and "IIntID" not in t.evidence["schema"]["missing_required_fields"]
            for t in (deaths[0], indicators[0]))):
        left, right = deaths[0].identifiers, indicators[0].identifiers
        linkage = {"status": "observed", "matched_unique_identifiers": len(left.keys() & right.keys()),
                   "deaths_only_identifiers": len(left.keys() - right.keys()),
                   "indicators_only_identifiers": len(right.keys() - left.keys()),
                   "one_to_one": all(count == 1 for count in (*left.values(), *right.values()))}
    write_json(work / ("inventory-observations.json" if inventory_only else "observations.json"), {
        "python_version": platform.python_version(), "inputs": [t.evidence for t in tables],
        "linkage": linkage, "config_digest": config_digest(config),
    })
    if any(t.evidence["status"] == "unreadable_or_malformed" for t in tables):
        raise EvidenceError("Some inputs could not be inspected. Review fixed-status observations and private parsing settings.")


def release_number(value: Any) -> str:
    if value is None:
        return "unresolved / not available"
    if type(value) is not int or value < 0:
        raise EvidenceError("Invalid aggregate evidence; rerun inspection.")
    return str(value)


def release_choice(
    value: Any,
    allowed: tuple[str, ...],
    *,
    document: Literal["review.json", "observations.json"],
    field: str,
) -> str:
    """Validate a category, reporting only caller-controlled field names and choices."""
    if not isinstance(value, str) or value not in allowed:
        recovery = (
            "Edit review.json, then rerun summary."
            if document == "review.json"
            else "Rerun inspect, then summary; do not edit generated observations."
        )
        raise EvidenceError(
            f"{document}: {field} must be one of: {', '.join(allowed)}. {recovery}"
        )
    return value


def summary(work: Path) -> None:
    (work / "candidate-summary.md").unlink(missing_ok=True)
    config = inventory_config(work)
    observed = read_json(work / "observations.json")
    if observed.get("config_digest") != config_digest(config):
        raise EvidenceError("Inventory changed after inspection; rerun inspect before reviewing a summary.")
    review = read_json(work / "review.json")
    sections = review.get("release_sections", {})
    if not isinstance(sections, dict) or any(type(sections.get(s)) is not bool for s in RELEASE_SECTIONS):
        raise EvidenceError("Set each release_sections entry to true or false after private review.")
    lines = ["# Candidate input-evidence summary", "",
             "PRIVATE DRAFT — manual review and transfer required. This file is not automatically approved.", "",
             "## Documentary expectations", "",
             "The accepted interface is two UTF-8 CSV inputs with IIntID, cause1_InterVA, Age_in_years "
             "and the 353 documented indicators. JSON v1 supplies the name comparison; the PDF describes v2. "
             "Matching older names does not establish v2 equivalence.", "",
             "Automated observations use user-declared parsing and exact strings. They do not establish "
             "native identifier fidelity, age semantics or missing/undetermined meanings.", ""]
    blockers = []
    for topic in REVIEW_TOPICS:
        decision = review.get(topic)
        if not isinstance(decision, dict):
            raise EvidenceError("Review is missing a required topic.")
        status = release_choice(
            decision.get("status"), REVIEW_STATUSES,
            document="review.json", field=f"{topic}.status",
        )
        approved = decision.get("release_approved")
        statement = decision.get("release_statement")
        if type(approved) is not bool or not isinstance(statement, str):
            raise EvidenceError("Review needs a release_statement string and release_approved boolean.")
        if status == "user_confirmed" and not str(decision.get("private_evidence", "")).strip():
            raise EvidenceError("User-confirmed topics require a private evidence reference, retained privately.")
        lines.extend([f"## {topic}", ""])
        if approved and statement.strip():
            lines.extend([f"Verification: {status}. User-approved release statement:", ""])
            # Quote only text the user explicitly selected for release; never private_evidence.
            lines.extend("> " + line for line in statement.splitlines())
            lines.append("")
        else:
            lines.extend(["Verification: unresolved for handoff; no approved statement supplied.", ""])
        if status != "user_confirmed" or not approved or not statement.strip():
            blockers.append(f"Resolve and approve {topic} for the input contract.")
    lines.extend(["## Selected automated observations", ""])
    if sections["inventory"]:
        version = observed["python_version"]
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise EvidenceError("Invalid runtime evidence; rerun inspection.")
        lines.extend([f"Listed input files: {len(observed['inputs'])}. Observed Python version: {version}.", ""])
    for index, item in enumerate(observed["inputs"], 1):
        status = release_choice(
            item["status"], ("observed", "unsupported", "unreadable_or_malformed", "serialization_unresolved"),
            document="observations.json", field=f"inputs[{index - 1}].status",
        )
        if any(sections.values()):
            lines.extend([f"### Input {index}", "", f"Inspection status: {status}.", ""])
        if status != "observed" and (sections["inventory"] or sections["serialization"]):
            blockers.append(f"Input {index}: inspection is unsupported or incomplete; specify preparation and reinspection.")
        if sections["inventory"]:
            for key, choices in (
                ("role", ROLES), ("declared_format", FORMATS),
                ("declared_organisation", ORGANISATIONS), ("observed_container", CONTAINERS),
            ):
                if key in item:
                    choice = release_choice(
                        item[key], choices, document="observations.json",
                        field=f"inputs[{index - 1}].{key}",
                    )
                    lines.append(f"- {key}: {choice}")
            lines.append("")
        if status != "observed":
            continue
        if sections["serialization"]:
            parsing = parsing_config({"serialization": item["parsing"]})
            lines.append("Declared parsing settings (successful parsing alone does not verify correctness):")
            lines.extend(f"- {key}: {value}" for key, value in parsing.items())
            lines.append("")
        schema = item["schema"]
        if sections["schema"]:
            for key in ("expected_fields", "observed_fields", "extra_field_count", "predictors_present"):
                lines.append(f"- {key}: {release_number(schema[key])}")
            for key in ("missing_documented_fields", "missing_required_fields"):
                names = schema[key]
                allowed = set(SCHEMA["deaths"] + SCHEMA["indicators"])
                if not isinstance(names, list) or any(not isinstance(n, str) or n not in allowed for n in names):
                    raise EvidenceError("Invalid schema evidence; rerun inspection.")
                lines.append(f"- {key}: {', '.join(names) if names else 'none'}")
            lines.append("")
        counts = item["counts"]
        if sections["characteristics"]:
            lines.extend(f"- {key}: {release_number(counts[key])}" for key in COUNT_FIELDS)
            lines.append("")
        if sections["schema"] and schema["missing_required_fields"]:
            blockers.append(f"Input {index}: required schema fields are missing.")
        if sections["characteristics"] and counts["rows"] == 0:
            blockers.append(f"Input {index}: no records were observed.")
        for key in ("blank_identifiers", "declared_missing_identifiers", "duplicate_identifier_groups",
                    "conflicting_target_identifiers", "indicator_unexpected"):
            if sections["characteristics"] and counts.get(key):
                blockers.append(f"Input {index}: resolve {key}; no automatic repair was performed.")
        if (sections["characteristics"] and counts["indicator_blank"]
                and config["indicator_blank_mapping"] != "missing_inapplicable"):
            blockers.append(f"Input {index}: indicator blanks need an explicit preparation decision.")
    linkage = observed["linkage"]
    if sections["characteristics"]:
        lines.extend(["### Linkage", ""])
        lines.append("Distinct exact-string keys; blank and declared missing identifiers are excluded. "
                     "Counts are provisional while identifier conventions remain unresolved.")
        if linkage["status"] == "observed":
            for key in ("matched_unique_identifiers", "deaths_only_identifiers", "indicators_only_identifiers"):
                lines.append(f"- {key}: {release_number(linkage[key])}")
            if type(linkage["one_to_one"]) is not bool:
                raise EvidenceError("Invalid linkage evidence; rerun inspection.")
            lines.append(f"- one_to_one: {linkage['one_to_one']}")
        else:
            lines.append("Linkage unresolved: requires exactly one successfully inspected table per role with IIntID.")
        lines.append("")
    if sections["characteristics"] and (linkage["status"] != "observed" or not linkage.get("one_to_one")):
        blockers.append("Establish unambiguous linkage after any explicit preparation.")
    if sections["characteristics"] and any(config["missing_tokens"][field] is None for field in ("identifier", "age", "target")):
        blockers.append("Missing-token conventions remain unresolved in the inspection configuration.")
    if sections["characteristics"] and config["indicator_blank_mapping"] == "unresolved":
        blockers.append("Indicator blank handling remains unresolved.")
    if not all(sections.values()):
        blockers.append("One or more evidence sections were withheld; provide reviewed evidence needed by Ticket 02.")
    lines.extend(["## Handoff and unresolved questions", "",
                  "Ticket 02 remains blocked until the user reviews and manually transfers the approved evidence "
                  "and resolves input-contract questions. No benchmark was fitted.", ""])
    lines.extend(f"- {blocker}" for blocker in blockers)
    if not blockers:
        lines.append("No automated contract blockers found; human release review is still required.")
    (work / "candidate-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (work / "candidate-summary.md").chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "inventory", "inspect", "summary"))
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "init":
            initialize(args.work_dir)
        elif args.command == "summary":
            summary(args.work_dir)
        else:
            inspect_inputs(args.work_dir, inventory_only=args.command == "inventory")
    except EvidenceError as error:
        print(str(error))
        return 2
    except (OSError, ValueError, TypeError, KeyError, csv.Error, StopIteration, EOFError):
        print("Unable to complete evidence command: check private configuration, input format and permissions.")
        return 2
    print("Private evidence command completed. No evidence has been released.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
