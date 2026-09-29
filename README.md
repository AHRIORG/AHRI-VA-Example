# AHRI-VA-Example

A Python project for reproducing recorded InterVA5 first-cause assignments from harmonised verbal-autopsy indicators for adult deaths aged 18 years or older in the documented 2000–2024 study period.

The research outcome is **replication agreement**: how closely simple classifiers reproduce existing InterVA5 assignments. Agreement does not establish accuracy against independently determined causes of death. The intended use is population research and research review.

## Current status

Tickets 01–03 are complete. The [private input-evidence wizard](docs/private-input-evidence.md) and the user-transferred [approved evidence summary](docs/issues/interva5-replication/reviewed-input-evidence.md) establish the reviewed input settings. `ahri-va validate` checks input integrity, exact linkage, adult/label eligibility, rare-class exclusions and partition feasibility without fitting models. `ahri-va benchmark` applies the same checks and prints the most-frequent-training-label baseline report. Logistic regression and the full three-model comparison remain for Tickets 04 and 05.

See the [validation guide](docs/validation.md) for the input contract and the [baseline benchmark guide](docs/benchmark.md) for installation, invented examples, report interpretation and offline transfer. Python 3.11+ is required. Runtime dependencies, including scikit-learn, are pinned; the [configuration template](config/validation.example.json) is unchanged.

Start with the [benchmark specification](docs/issues/interva5-replication/spec.md) and [Ticket 01 completion record](docs/issues/interva5-replication/issues/01-private-input-evidence-wizard.md#completion-record--29-september-2026). The user confirmed the input formats, key meanings and `[""]` missing-token lists for identifiers, ages and targets. Blank indicators follow the accepted rejection rule unless an explicit mapping is reviewed. The handoff contains the reviewed basis for Ticket 02's input contract.

## Accepted benchmark design

| Aspect | Planned behaviour |
| --- | --- |
| Input interface | Two UTF-8 CSV files: harmonised indicators and the companion deaths table. The user-confirmed formats and parsing declarations are recorded in the approved evidence summary. |
| Target and linkage | Reproduce `cause1_InterVA`, linking the tables losslessly through `IIntID`. Duplicate identifiers or conflicting targets stop the run; unmatched records are excluded and counted. |
| Adult eligibility | Use `Age_in_years >= 18`; the user confirmed completed age at death and an empty-string missing token. Exclude and count missing or invalid ages. |
| Predictors | Use the 353 documented harmonised indicators. Exclude identifiers, metadata, algorithm outputs and the five additional COVID fields. Keep `y`, `n` and `-` distinct; `-` represents missing/inapplicable information. |
| Target classes | Preserve exact labels, including a documented explicit undetermined assignment. Exclude absent/unusable targets. Before splitting, remove classes with fewer than five eligible labelled adults and require at least two retained classes. |
| Models | Compare a most-frequent-training-label baseline, regularised multinomial logistic regression and a random forest, with the fixed tuning budget in the specification. |
| Evaluation | Use an approximately 80/20 stratified development/test split, three-fold development cross-validation and seed 42. Check class coverage explicitly; preprocessing, tuning and learner selection use training data only. |
| Output | Produce a concise Markdown report with exact-match agreement, macro F1, per-cause recall and support, exclusions, retained population coverage and reproducibility details. |

Results describe the retained benchmark population. Five eligible examples is a feasibility cutoff, not a guarantee of reliable per-cause estimates. Technical completion requires correct software behaviour and a valid report, with no promised agreement threshold.

## Development and private execution

Development in this account uses source code, documentation and invented teaching fixtures. Tests may fit disposable models and inspect predictions derived exclusively from invented records.

Participant records, private contracts or reports, raw logs, individual predictions and fitted models derived from real records must remain outside this development account. Only the user runs real-data commands in the separate analysis account; no agent runs there. Real-data reports remain private until the user releases reviewed aggregates. The benchmark will keep intermediate predictions in memory and will not export individual predictions or fitted models.

Ticket 01 provides the controlled handoff for input evidence: the user runs the wizard privately, reviews its limited summary of format/schema facts, conventions and aggregate checks, and transfers only the approved summary into this repository. Private paths, record excerpts and raw logs stay private. Unresolved assumptions remain explicit.

See [AGENTS.md](AGENTS.md) for the development rules. Instructions and Git ignores do not enforce access controls.

## Implementation sequence

Tickets are tracked as local Markdown files, following the [issue-tracker conventions](docs/agents/issue-tracker.md) and [triage vocabulary](docs/agents/triage-labels.md).

1. [HITL: Create and run a private input-evidence wizard](docs/issues/interva5-replication/issues/01-private-input-evidence-wizard.md) — complete, including private execution, approved evidence transfer and recorded missing-value conventions.
2. [Validate inputs and identify eligible labelled adults](docs/issues/interva5-replication/issues/02-validate-inputs-and-adult-eligibility.md) — complete, using the reviewed evidence from Ticket 01; see the [validation guide](docs/validation.md).
3. [Run a baseline benchmark with population and partition checks](docs/issues/interva5-replication/issues/03-baseline-and-partition-checks.md) — complete; see the [baseline guide](docs/benchmark.md).
4. [Add training-only logistic-regression selection](docs/issues/interva5-replication/issues/04-logistic-regression-selection.md).
5. [Complete the random-forest comparison and benchmark report](docs/issues/interva5-replication/issues/05-random-forest-and-complete-report.md).

Dependencies follow **01 → 02 → 03 → 04 → 05**. Creating the wizard alone does not complete Ticket 01: the reviewed evidence handoff must also occur. Ticket readiness does not override blockers or authorize later implementation.

## Ticket 01 tooling

The [execution guide](docs/private-input-evidence.md) covers prerequisites, all six stages, captured values and private review/transfer. Bash and Python 3.11+ are sufficient; the runtime uses only the Python standard library and works offline. The interactive wizard is for the human in the analysis account. Development checks use invented records only:

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n scripts/private-input-wizard.sh
```

The wizard template library is preserved unchanged from the `wizard` skill. The repository includes the user-approved evidence summary. Participant inputs and private working evidence remain outside this account.

An offline transfer archive can be built from the reviewed source with `python3 scripts/build_transfer_bundle.py --output dist/ahri-va-ticket01.tar.gz --revision <full-commit-sha>`. It uses an explicit source/documentation allowlist and includes `START-HERE.md`, invented tests and checksums. Build only from the reviewed committed files so the recorded revision identifies its contents. The archive assumes the user's confirmed destination runtime: the same Mac with Bash and Python 3.11+.

## Supporting documentation

- [Domain glossary](CONTEXT.md) — shared terminology for records, labels, replication agreement and the benchmark population.
- [Accepted design interview](docs/design-interview.md) — the agreed protocol and decisions.
- [Input-specification review](docs/input-spec-review.md) — documentary findings and unresolved private-input assumptions, including the JSON-v1/PDF-v2 distinction.
- [ADR 0001: Replicate InterVA5 first cause](docs/adr/0001-replicate-interva5-first-cause.md) and [ADR 0002: Exclude infeasible cause classes](docs/adr/0002-exclude-infeasible-cause-classes.md) — accepted architectural decisions.
- [JSON input specification](docs/data_specs/AHRI.VerbalAutopsy.Harmonisation.json) and [PDF data dictionary](docs/data_specs/VerbalAutopsy.Harmonisation_Data.pdf) — supplied documentation, not participant inputs or proof of actual-file contents.
