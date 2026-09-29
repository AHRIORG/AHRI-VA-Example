# 02 — Validate inputs and identify eligible labelled adults

Status: ready-for-agent
Progress: resolved

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** None — [Ticket 01](01-private-input-evidence-wizard.md) is resolved. The user authorized implementation on 29 September 2026.

**Reviewed evidence received:** [Approved input-evidence summary](../reviewed-input-evidence.md) and [Ticket 01 completion record](01-private-input-evidence-wizard.md#completion-record--29-september-2026). The user confirmed `[""]` as the declared missing-token list for each of `IIntID`, `Age_in_years` and `cause1_InterVA`. Match tokens exactly. Reject blank indicators under the accepted rule, keep `-` as missing/inapplicable, and retain the exact target label `Undetermined` as a class. The summary confirms v2 fields, lossless identifier preservation, completed age at death and two UTF-8 CSV inputs; no additional conversion is required. These facts and settings come from the user's release and handoff discussion, not from invented-fixture tests or inferred zero counts.

**What to build:** A usable Python `validate` command that accepts the agreed two UTF-8 CSV inputs plus explicit configuration, checks their integrity and reports how many records have an unambiguous link, adult eligibility and a usable InterVA5 first-cause label. The configuration template and preparation guidance use Ticket 01's reviewed evidence; invented examples demonstrate the complete command without accessing participant records.

## Acceptance criteria

- [x] Deliver an installable Python command-line package with pinned dependencies, a configuration template, invented examples and concise usage guidance. Demonstrate the installed `validate` command with invented inputs; it performs no model fitting.
- [x] Use the transferred evidence to document input preparation, required fields, identifier handling, age semantics and missing/undetermined conventions. Keep any remaining unknowns explicit. If private formats require preparation, explain the reviewed conversion requirements without silently expanding the supported interchange contract or changing the scientific design.
- [x] Accept the two UTF-8 CSV tables under the declared parsing rules. Missing required columns, malformed records, invalid configuration and undeclared indicator values fail validation with actionable field names and aggregate counts, without participant values or record excerpts.
- [x] Restrict predictors to the explicit 353-indicator allowlist. Keep `y`, `n` and `-` distinct, with `-` representing missing/inapplicable information. Accept blanks only through an explicitly reviewed mapping. Exclude identifiers, targets, metadata, prior algorithm outputs and the five COVID extras from predictors.
- [x] Parse `IIntID` losslessly, with any normalisation explicit. Duplicate identifiers, ambiguous linkage or conflicting target records stop validation. Require one-to-one linkage and exclude/count unmatched records without double-counting exclusions.
- [x] Apply `Age_in_years >= 18` using the reviewed completed-age-at-death convention. Exclude and count missing/invalid ages and absent/unusable targets. Retain the documented explicit undetermined assignment as a class and preserve exact target labels without pooling or relabelling.
- [x] Return a clear input/eligibility validation outcome and reconcilable aggregate counts. This milestone does not claim that rare-class or partition feasibility has been established; Ticket 03 adds those checks to validation.
- [x] Verify behaviour through the public command boundary using temporary invented CSVs and fixture configuration, plus a packaging smoke check. Cover the age-18 boundary, missing/invalid ages and targets, explicit undetermined labels, all indicator states, reviewed/unreviewed blank mappings, malformed inputs, leading-zero and large-digit keys, duplicates, conflicts and unmatched records.
- [x] Verify the predictor boundary using invented records and ensure diagnostics contain no record values. Tests must not load packaged participant datasets, private evidence artifacts or real-data-derived artifacts.

## Execution boundary

The user authorized Ticket 02 implementation on 29 September 2026. Development uses source, documentation, the user-released evidence summary and invented fixtures only; the user alone executes real-data commands in the separate analysis account.


## Completion record — 29 September 2026

Implemented the installable `ahri-va validate` command and equivalent
`python -m ahri_va validate` entry point. The [validation guide](../../../validation.md)
contains installation, the reviewed preparation/serialization rules, configuration,
count reconciliation and private-execution instructions. The
[configuration template](../../../../config/validation.example.json) preserves the
released missing-token lists and rejects indicator blanks by default. Future
blank-to-missing mappings require an explicit review declaration.

The command uses a packaged, fixed 353-indicator allowlist, exact-string identifiers
and labels, one-to-one linkage, and sequential missing/invalid-age, under-18 and
missing/unusable-target exclusions. Missing keys and unmatched records are counted
separately per input. Duplicate keys, conflicting targets, undeclared indicator
values and malformed inputs fail with value-free diagnostics. No models are
fitted or exported; the output explicitly marks benchmark feasibility unchecked.
The reusable eligibility result keeps only predictor categories and exact targets
in memory for later tickets.

Verification on Python 3.14.6:

- `python3 -m unittest discover -s tests -v`: **37 tests passed**, including 23
  validation-command tests and the 14 existing evidence-tooling tests. All records
  were invented, and the command tests ran in process with a fresh-process module
  entry-point check.
- Built `ahri_va-0.2.0-py3-none-any.whl` with the pinned build dependencies,
  installed it offline into a fresh virtual environment, and ran the installed
  command outside the repository. The generated invented example returned the
  expected eight matched records, three eligible adults, one undetermined
  assignment and one record in each of the five eligibility exclusion categories.
- Reviewed the feature boundary and diagnostic paths; tests cover leading-zero
  and large-digit keys, exact token matching and label preservation, all three
  indicator states, extra-field perturbations, blank mappings, malformed quoting,
  UTF-8 errors, duplicate headers, conflicts and output-artifact absence.
- Whitespace checks pass for the changed ticket, README and ignore rules. An
  existing unrelated edit in `docs/course/initial prompt.txt` was left untouched.

The runtime and tests use only the Python standard library; build dependencies
are pinned in `pyproject.toml` and `requirements-build.txt`. Only invented inputs
were executed. No participant input, private working evidence or real-data
artifact was opened. Ticket 03 is now dependency-unblocked but remains outside
this implementation authorization.

## Comments

29 September 2026: After transfer and installation in the separate analysis
account, the user reported: “Wheel validated successfully on real data.” This
records the user's confirmation of successful private execution of the Ticket 02
validator. No participant records, private configuration, command output or
aggregate counts were supplied or inspected in this follow-up. Rare-class and
partition feasibility remain unchecked until Ticket 03; no replication model
was fitted by this command.
