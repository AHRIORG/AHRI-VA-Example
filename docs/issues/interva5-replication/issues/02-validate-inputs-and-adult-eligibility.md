# 02 — Validate inputs and identify eligible labelled adults

Status: ready-for-agent
Progress: open

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** None — [Ticket 01](01-private-input-evidence-wizard.md) is resolved. Implementation remains deferred to the user's next session.

**Reviewed evidence received:** [Approved input-evidence summary](../reviewed-input-evidence.md) and [Ticket 01 completion record](01-private-input-evidence-wizard.md#completion-record--29-september-2026). The user confirmed `[""]` as the declared missing-token list for each of `IIntID`, `Age_in_years` and `cause1_InterVA`. Match tokens exactly. Reject blank indicators under the accepted rule, keep `-` as missing/inapplicable, and retain the exact target label `Undetermined` as a class. The summary confirms v2 fields, lossless identifier preservation, completed age at death and two UTF-8 CSV inputs; no additional conversion is required. These facts and settings come from the user's release and handoff discussion, not from invented-fixture tests or inferred zero counts.

**What to build:** A usable Python `validate` command that accepts the agreed two UTF-8 CSV inputs plus explicit configuration, checks their integrity and reports how many records have an unambiguous link, adult eligibility and a usable InterVA5 first-cause label. The configuration template and preparation guidance use Ticket 01's reviewed evidence; invented examples demonstrate the complete command without accessing participant records.

## Acceptance criteria

- [ ] Deliver an installable Python command-line package with pinned dependencies, a configuration template, invented examples and concise usage guidance. Demonstrate the installed `validate` command with invented inputs; it performs no model fitting.
- [ ] Use the transferred evidence to document input preparation, required fields, identifier handling, age semantics and missing/undetermined conventions. Keep any remaining unknowns explicit. If private formats require preparation, explain the reviewed conversion requirements without silently expanding the supported interchange contract or changing the scientific design.
- [ ] Accept the two UTF-8 CSV tables under the declared parsing rules. Missing required columns, malformed records, invalid configuration and undeclared indicator values fail validation with actionable field names and aggregate counts, without participant values or record excerpts.
- [ ] Restrict predictors to the explicit 353-indicator allowlist. Keep `y`, `n` and `-` distinct, with `-` representing missing/inapplicable information. Accept blanks only through an explicitly reviewed mapping. Exclude identifiers, targets, metadata, prior algorithm outputs and the five COVID extras from predictors.
- [ ] Parse `IIntID` losslessly, with any normalisation explicit. Duplicate identifiers, ambiguous linkage or conflicting target records stop validation. Require one-to-one linkage and exclude/count unmatched records without double-counting exclusions.
- [ ] Apply `Age_in_years >= 18` using the reviewed completed-age-at-death convention. Exclude and count missing/invalid ages and absent/unusable targets. Retain the documented explicit undetermined assignment as a class and preserve exact target labels without pooling or relabelling.
- [ ] Return a clear input/eligibility validation outcome and reconcilable aggregate counts. This milestone does not claim that rare-class or partition feasibility has been established; Ticket 03 adds those checks to validation.
- [ ] Verify behaviour through the public command boundary using temporary invented CSVs and fixture configuration, plus a packaging smoke check. Cover the age-18 boundary, missing/invalid ages and targets, explicit undetermined labels, all indicator states, reviewed/unreviewed blank mappings, malformed inputs, leading-zero and large-digit keys, duplicates, conflicts and unmatched records.
- [ ] Verify the predictor boundary using invented records and ensure diagnostics contain no record values. Tests must not load packaged participant datasets, private evidence artifacts or real-data-derived artifacts.

## Execution boundary

Implementation remains deferred until authorized. Ticket readiness does not remove its blocker. Development uses source, documentation, the user-released evidence summary and invented fixtures only; the user alone executes real-data commands in the separate analysis account.
