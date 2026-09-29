# 01 — HITL: Create and run a private input-evidence wizard

Status: ready-for-human
Progress: claimed

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** Final missing-value decisions listed in the [handoff review](#handoff-review--29-september-2026).

**What to build:** An interactive Bash wizard, created using the `$wizard` skill, that helps the user establish the actual input files' formats and the characteristics needed for the adult InterVA5 first-cause replication benchmark. The agent develops and verifies the tooling using invented teaching fixtures. The user runs it in the separate private analysis account, reviews its evidence summary and transfers only the approved summary into this repository for subsequent tickets.

## Ordered wizard stages

1. **Input inventory:** the user identifies the local inputs and available runtime; gather the actual file count, native formats, compression, table/sheet organisation and available release/version evidence. Do not assume that the private inputs are already two CSV files. Private source locations remain in the analysis account.
2. **Serialization:** establish encoding, delimiter, quoting/escaping, header layout and blank/null serialization where applicable. Distinguish observed properties from inferred or user-confirmed properties; record unsupported formats and unknowns explicitly.
3. **Schema compatibility:** compare the observed schema with the documented v2 deaths and harmonised-indicator tables. Check the 353-indicator allowlist, `IIntID`, `cause1_InterVA` and `Age_in_years`. Matching older documentation alone does not confirm v2 equivalence.
4. **Required characteristics:** gather aggregate checks for identifier completeness, lossless representation, uniqueness, linkage, conflicting targets, indicator codes and missing-value handling. Ask the user to confirm completed-age-at-death semantics and the exact missing/undetermined conventions from private evidence. Automated observations cannot establish those meanings by themselves.
5. **Preparation requirements:** record any conversion or explicit mapping needed to produce the supported two UTF-8 CSV inputs, including preservation of identifiers, indicator states and exact target labels. Record unresolved questions without silently inventing normalisation or changing the accepted benchmark protocol.
6. **Review and handoff:** present a deliberately limited evidence summary for the user's review. It contains approved format/schema facts, required conventions and aggregate checks, with verification status, preparation decisions and unresolved questions. The user decides what may leave the analysis account and manually transfers the approved summary into this repository.

## Acceptance criteria

- [x] Read and use the `$wizard` skill when implementing. Preserve its template library and author only the task stages. Provide focused instructions, progress estimates, confirmation gates and a closing summary; make the wizard executable.
- [x] Before authoring, make each stage's captured values, evidence sources, destinations and private/releasable classification concrete with the user. Provide verifiable commands or manual instructions; do not invent an unknown native format, interface or tool capability.
- [x] Bash orchestrates the human procedure; all data-inspection computations run in Python. The user alone executes real-data commands in the analysis account; no agent runs there. The agent never opens private inputs or private evidence artifacts.
- [x] Keep private working evidence separate from the proposed release summary. Do not automatically transfer, commit or upload evidence. Exclude participant values, record excerpts, private paths, raw logs, private contracts/reports, individual predictions and fitted models from the released material. Include only user-approved format/schema facts, conventions and aggregate checks needed by later tickets.
- [x] Preserve the distinction between confirmed facts, documentary expectations, automated observations and unresolved assumptions. Unexpected codes or conflicts remain actionable findings rather than being silently repaired. No benchmark fitting is required for this ticket.
- [x] Run Bash syntax validation and ShellCheck when available; statically trace captured values to their intended destinations. Verify Python inspection and summary-generation behaviour with invented fixtures only, including malformed/unsupported inputs and omission of record values from the proposed summary. Do not run the interactive wizard end to end as an agent.
- [x] Supply clear private-execution, review and transfer instructions. The user runs the wizard, reviews the summary and transfers the approved evidence into this repository. Link that evidence from this ticket when completing it; script creation alone does not complete the ticket.
- [ ] The evidence gives Ticket 02 a reviewed basis for its input contract and preparation guidance. Any unresolved matter that prevents implementing that contract remains an explicit blocker requiring a user decision; no actual-input fact is inferred from invented-fixture tests.

## Execution boundary

This is a human-in-the-loop ticket with agent-authored tooling. The user authorized Ticket 01 implementation on 29 September 2026 and confirmed the six-stage capture plan and Python command testing boundary. Source, documentation and invented fixtures are the only development inputs; instructions and Git ignores do not enforce access controls. Human execution, release review and evidence transfer remain required for completion.

## Comments

29 September 2026: Agent-authored tooling is available in the [execution guide](../../../private-input-evidence.md), [wizard](../../../../scripts/private-input-wizard.sh) and [Python inspector](../../../../scripts/input_evidence.py). The guide records the user-confirmed capture/destination plan. The wizard library is byte-identical to the supplied template above the stages marker. Bash syntax, Python typechecking and command tests use invented fixtures only; ShellCheck was not installed. The interactive wizard was not run by an agent.

The user also requested an offline transfer archive and confirmed the destination is the same Mac with Bash and Python 3.11+ already available. The [bundle builder](../../../../scripts/build_transfer_bundle.py) packages an explicit allowlist of source, documentation and invented tests with checksums; no runtime packages or network access are needed.

Code review compared this work with `bc71f02335e1326b59d16d1d0f775c7fa08e4e61` on separate standards and spec axes. The standards review found duplicated categorical choices (P3 heuristic), now shared. The spec review found detailed blocker messages bypassed section opt-outs (P2), now gated by the same release choices and covered by an invented-command regression test. No actual-input conclusions were drawn.

**Human handoff received:** the user privately ran the tooling and transferred the [approved evidence summary](../reviewed-input-evidence.md). The final input-contract decisions below remain open, so this ticket remains claimed and Ticket 02 remains blocked. Actual-input facts below come from the user's release, not from invented-fixture tests.

Stage 6 follow-up: the user reported the generic `Invalid categorical evidence; rerun inspection.` message. Invented command fixtures reproduced it for both invalid review statuses and invalid generated observation categories; the private trigger was not inspected. Diagnostics now name only the known document/field and allowed choices, with recovery appropriate to that document. A review-status correction can be retried through `summary` without rerunning inspection or losing saved review work. The [guide](../../../private-input-evidence.md#recovering-a-stage-6-category-error) documents recovery.

## Handoff review — 29 September 2026

The user marked the summary `APPROVED FOR RELEASE`, transferred it as `candidate-summary.md`, and authorized checking, committing and pushing it. It is stored as [reviewed-input-evidence.md](../reviewed-input-evidence.md); only the document title was changed. Its generated handoff wording reflects the state before transfer. This review records the current state.

The released statements confirm v2 compatibility, preservation of original `IIntID` values, completed age at death, empty age/target cells as missing, the exact undetermined-assignment label `Undetermined`, and two UTF-8 CSV inputs requiring no conversion. Both tables use comma delimiters, double quotes, doubled-quote escaping, no separate escape character and a first-record header. All documented fields are present, including the 353 indicators.

The approved aggregates are internally consistent: 26,168 matched identifiers plus 1,558 deaths-only identifiers equal 27,726 deaths records. The indicator-state counts total 9,237,304 cells, equal to 26,168 records × 353 indicators. No duplicate identifiers, conflicting targets, indicator blanks or unexpected indicator codes were reported. These checks used only the released summary; no participant inputs or private working evidence were opened.

**Indicator-blank clarification:** the released summary reports zero blank indicator cells and an unresolved `indicator_blank_mapping` setting. The [accepted encoding rule](../spec.md#implementation-decisions) already requires rejection of undeclared values and permits blanks only through an explicitly reviewed mapping. Ticket 02 can therefore reject blank indicators without another private-data check or a new protocol decision. A future mapping to the missing/inapplicable indicator response would require separate evidence and approval. The earlier handoff review overstated the unresolved setting as a new blocker; this paragraph corrects that interpretation without changing the approved summary.

The wizard should have shown the observed blank count, explained the accepted rejection rule, captured any explicit mapping choice, and included the approved handling rule in the summary. The example missing-conventions release statement covered age/target blanks but omitted indicator handling, which contributed to the unclear handoff.

**Remaining contract question — complete missing-token lists:** confirm the exact, exhaustive missing tokens for `IIntID`, `Age_in_years` and `cause1_InterVA`. The release confirms empty age/target cells mean missing, but does not say these are the only tokens or specify the identifier convention. Zero declared-missing counts cannot establish those lists. Preserve `Undetermined` as a target class, distinct from an absent label.

The user will resume later with Ticket 02. No Ticket 02 implementation was started. Keep the remaining acceptance item open until the complete missing-token conventions are recorded; do not infer them from the observed counts.
