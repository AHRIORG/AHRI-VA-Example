"""Explicit, validated configuration for the reviewed CSV interchange."""

from dataclasses import dataclass
import json
from pathlib import Path


__all__ = ["Configuration", "ValidationError", "load_configuration"]

_SERIALIZATION = {
    "encoding": "utf-8", "delimiter": "comma", "quote": "double",
    "escape": "none", "doublequote": True, "header_row": 1,
}
_FIELDS = {
    "schema_version", "serialization", "identifier_normalization",
    "age_semantics", "missing_tokens", "undetermined_label",
    "indicator_blank_mapping", "indicator_blank_mapping_reviewed",
}


class ValidationError(ValueError):
    """A value-free diagnostic that can safely cross the command boundary."""


@dataclass(frozen=True)
class Configuration:
    """Exact missing tokens and the explicitly declared indicator-blank rule."""

    identifier_missing: frozenset[str]
    age_missing: frozenset[str]
    target_missing: frozenset[str]
    map_indicator_blanks: bool
    undetermined_label: str


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("configuration: duplicate JSON fields; use unique fields.")
        result[key] = value
    return result


def _missing_tokens(value: object, field: str) -> frozenset[str]:
    if (not isinstance(value, list)
            or any(not isinstance(token, str) for token in value)
            or "" not in value
            or len(set(value)) != len(value)):
        raise ValidationError(
            f"missing_tokens.{field}: require unique exact strings including the empty string."
        )
    return frozenset(value)


def load_configuration(path: Path) -> Configuration:
    """Read explicit settings, rejecting unsupported or ambiguous configuration.

    Args:
        path: JSON configuration, with every field declared as in the template.

    Returns:
        Settings using exact-string tokens and no implicit normalization.

    Raises:
        ValidationError: Unreadable JSON or invalid configuration. Messages do
            not include paths, unknown keys or supplied values.
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ValidationError):
            raise
        raise ValidationError("configuration: cannot read valid UTF-8 JSON.") from None
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValidationError("configuration: missing or unknown fields; use the complete template.")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValidationError("schema_version: require version 1.")
    parsing = value["serialization"]
    if (not isinstance(parsing, dict) or parsing != _SERIALIZATION
            or type(parsing.get("header_row")) is not int
            or type(parsing.get("doublequote")) is not bool):
        raise ValidationError(
            "serialization: require UTF-8, comma delimiter, double quotes, doubled-quote "
            "escaping, no separate escape character and a first-record header."
        )
    if value["identifier_normalization"] != "none":
        raise ValidationError("identifier_normalization: only none is supported for IIntID.")
    if value["age_semantics"] != "completed_years_at_death":
        raise ValidationError("age_semantics: require completed_years_at_death for Age_in_years.")
    if value["undetermined_label"] != "Undetermined":
        raise ValidationError("undetermined_label: require the reviewed label from the template.")
    missing = value["missing_tokens"]
    if not isinstance(missing, dict) or set(missing) != {"identifier", "age", "target"}:
        raise ValidationError("missing_tokens: declare identifier, age and target lists.")
    tokens = {field: _missing_tokens(missing[field], field) for field in missing}
    if value["undetermined_label"] in tokens["target"]:
        raise ValidationError("missing_tokens.target: cannot include the undetermined assignment.")
    mapping = value["indicator_blank_mapping"]
    reviewed = value["indicator_blank_mapping_reviewed"]
    if mapping not in ("reject", "missing_inapplicable") or type(reviewed) is not bool:
        raise ValidationError(
            "indicator_blank_mapping: choose reject or missing_inapplicable; "
            "indicator_blank_mapping_reviewed must be boolean."
        )
    if mapping == "missing_inapplicable" and not reviewed:
        raise ValidationError(
            "indicator_blank_mapping_reviewed: a missing_inapplicable mapping requires "
            "explicit private review; the current reviewed configuration rejects blanks."
        )
    return Configuration(
        identifier_missing=tokens["identifier"], age_missing=tokens["age"],
        target_missing=tokens["target"], map_indicator_blanks=mapping == "missing_inapplicable",
        undetermined_label=value["undetermined_label"],
    )
