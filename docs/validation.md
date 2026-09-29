# Validate inputs and adult eligibility

Ticket 02 delivers `ahri-va validate`. It checks input integrity, exact one-to-one
linkage and adult/target eligibility without fitting models. It does **not**
establish rare-class or partition feasibility; those checks belong to Ticket 03.
An empty eligible population can pass this milestone's input checks.

## Install and try invented records

Use Python 3.11 or newer. There are no third-party runtime or test dependencies;
the build dependencies are pinned in `requirements-build.txt` and `pyproject.toml`.
From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps .
python3 examples/write_invented_inputs.py --output-dir /tmp/ahri-va-invented-example
.venv/bin/ahri-va validate \
  --deaths /tmp/ahri-va-invented-example/deaths.csv \
  --indicators /tmp/ahri-va-invented-example/indicators.csv \
  --config config/validation.example.json
```

Choose a new output directory for each example run. The generator creates only
invented records and refuses to overwrite an existing directory. Its expected
result is 10 rows in each table, one missing identifier in each, one unmatched
record in each, eight matched records and three eligible labelled adults. The
five remaining matched records have one exclusion each: missing age, invalid
age, under 18, missing target and unusable target. One eligible assignment is
`Undetermined`; eligible indicator totals are `y: 3`, `n: 3`, `-: 1053`.

The equivalent module command is `.venv/bin/python -m ahri_va validate ...`.
Run the command tests using `python3 -m unittest discover -s tests -v`; all inputs
are created from invented fixtures in temporary directories.

To build an offline-installable wheel after installing the build dependencies:

```bash
.venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index . --wheel-dir dist
```

The resulting `dist/ahri_va-0.2.0-py3-none-any.whl` contains the predictor
allowlist. On the destination account, the user can install that wheel into a
virtual environment with `python -m pip install --no-index --no-deps <wheel>`.
Transfer the configuration template and this guide separately as needed. The
older Ticket 01 transfer-bundle builder packages only the evidence tooling.

## Reviewed input contract

The [approved evidence](issues/interva5-replication/reviewed-input-evidence.md)
and [Ticket 01 completion record](issues/interva5-replication/issues/01-private-input-evidence-wizard.md#completion-record--29-september-2026)
establish the current settings. Both inputs correspond to v2; their existing
UTF-8 CSV exports need no further conversion. The user confirmed original
identifier preservation, completed age **at death**, exact `Undetermined`
spelling and `[""]` as each missing-token list. These are user-reviewed facts,
not conclusions from invented tests or from observed zero counts.

| Setting | Supported rule |
| --- | --- |
| Serialization | UTF-8 without BOM; comma delimiter, double-quoted fields, doubled quotes inside quoted fields, no separate escape character, first record is the header. LF and CRLF work. |
| Deaths fields | `IIntID`, `Age_in_years`, `cause1_InterVA`. |
| Indicator fields | `IIntID` and every name in the fixed [353-field allowlist](../src/ahri_va/predictors.json). Column order is arbitrary. |
| Extra fields | Ignored, including metadata, previous algorithm outputs and five COVID extras. The allowlist cannot be replaced through configuration. |
| Identifiers | Exact strings, with no numeric conversion, trimming, case folding or other normalization. Leading zeros, large digit strings, decimal-like strings and exponent-like strings remain distinct. |
| Missing tokens | Match exactly, before interpreting the field; defaults are `[""]` for identifier, age and target. Other spellings are not inferred as missing. |
| Age | A finite nonnegative number of completed years. Whole-number decimal/exponent notation such as `18.0` or `1.8e1` is valid; fractions, negative values, non-numbers, whitespace and numeric separators are invalid. The adult boundary is exactly 18. No undocumented sentinel or upper-age cutoff is inferred. |
| Targets | Declared missing targets, whitespace-only strings and strings containing control characters are unusable. All other labels retain exact Unicode, case and surrounding spaces. `Undetermined` remains a class. No vocabulary or class pooling is invented. |
| Indicators | Exact `y`, `n` and `-` only; `-` means missing/inapplicable and remains distinct from negative. No trimming or case conversion. |

The allowlist is copied from the documentary `predictors` list in
`scripts/documented-schema.json` (JSON v1 F41); the reviewed handoff supplies the
v2 compatibility confirmation. Installed operation needs no repository or
documentary files beyond the packaged list.

All configuration fields are required, and unknown/duplicate JSON fields and
unsupported parsing settings are errors. Start from
[validation.example.json](../config/validation.example.json). Future changes to
missing-token lists need private review; the program cannot verify their meaning.
The configuration must keep the empty-string missing token and cannot declare
`Undetermined` missing.

Blank indicators currently fail. A future privately reviewed blank-to-`-` rule
can be declared with `indicator_blank_mapping: "missing_inapplicable"` and
`indicator_blank_mapping_reviewed: true`. Both settings are required for that
mapping; the flag is a declaration, not evidence that review occurred. A space
is not an empty cell and is still rejected. Mapping a blank to `n` or `y` is
unsupported.

## Validation order and counts

Both complete tables undergo header, record-width, UTF-8, quoting and key
integrity checks. Headers must be present, nonblank and unique. Fields over
131072 characters fail. All 353 indicators are checked in **every** indicator
record, including records that later fail linkage or eligibility. Duplicate
nonmissing identifiers fail even when targets agree or the keys are unmatched;
conflicting exact targets are reported as an additional aggregate error.

For structurally valid tables:

1. Exclude/count declared missing identifiers separately in each input. An
   undeclared whitespace-only identifier or one containing control characters
   fails validation; no replacement identifier is invented.
2. Link exact identifiers one-to-one and exclude/count unmatched records on
   each side.
3. Among matched records, exclude in this order: missing age, invalid age,
   age under 18, missing target, unusable target. Each record receives at most
   one exclusion reason.
4. Count the remaining eligible labelled adults, exact distinct classes,
   undetermined assignments and the three eligible indicator states.

For **each input**, `rows = missing_identifiers + unmatched + matched_records`.
For the matched population, `matched_records = sum(exclusions) +
eligible_labelled_adults`. Missing/invalid targets on an excluded age record do
not add another exclusion. Counts describe input/eligibility readiness only.

## Outcomes and private execution

Exit code **0** writes an aggregate JSON result to stdout with `status: "valid"`,
`scope: "input_integrity_and_adult_label_eligibility"`,
`benchmark_feasibility: "not_checked"` and `models_fitted: 0`.
Exit code **2** writes JSON errors to stderr naming known fields and aggregate
counts where available. Syntax/decoding failures report at least one detected
malformed record, not a complete count from an unreadable remainder. Neither
outcome echoes paths, identifiers, target labels, unexpected values or record
excerpts. No report, individual predictions or fitted models are written.

The user alone runs participant-input commands in the separate analysis
account, using private paths in place of the invented example paths. Validation
output stays in that account until the user reviews it for release. Software
checks cannot establish the meaning or completeness of future inputs, their
class/partition feasibility or the scientific validity of an eventual benchmark.
Instructions, configuration flags and Git ignores do not enforce access controls.
