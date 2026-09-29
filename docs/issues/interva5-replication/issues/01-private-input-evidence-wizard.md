# 01 — HITL: Create and run a private input-evidence wizard

Status: ready-for-human

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** None — can start when implementation is authorized.

**What to build:** An interactive Bash wizard, created using the `$wizard` skill, that helps the user establish the actual input files' formats and the characteristics needed for the adult InterVA5 first-cause replication benchmark. The agent develops and verifies the tooling using invented teaching fixtures. The user runs it in the separate private analysis account, reviews its evidence summary and transfers only the approved summary into this repository for subsequent tickets.

## Ordered wizard stages

1. **Input inventory:** the user identifies the local inputs and available runtime; gather the actual file count, native formats, compression, table/sheet organisation and available release/version evidence. Do not assume that the private inputs are already two CSV files. Private source locations remain in the analysis account.
2. **Serialization:** establish encoding, delimiter, quoting/escaping, header layout and blank/null serialization where applicable. Distinguish observed properties from inferred or user-confirmed properties; record unsupported formats and unknowns explicitly.
3. **Schema compatibility:** compare the observed schema with the documented v2 deaths and harmonised-indicator tables. Check the 353-indicator allowlist, `IIntID`, `cause1_InterVA` and `Age_in_years`. Matching older documentation alone does not confirm v2 equivalence.
4. **Required characteristics:** gather aggregate checks for identifier completeness, lossless representation, uniqueness, linkage, conflicting targets, indicator codes and missing-value handling. Ask the user to confirm completed-age-at-death semantics and the exact missing/undetermined conventions from private evidence. Automated observations cannot establish those meanings by themselves.
5. **Preparation requirements:** record any conversion or explicit mapping needed to produce the supported two UTF-8 CSV inputs, including preservation of identifiers, indicator states and exact target labels. Record unresolved questions without silently inventing normalisation or changing the accepted benchmark protocol.
6. **Review and handoff:** present a deliberately limited evidence summary for the user's review. It contains approved format/schema facts, required conventions and aggregate checks, with verification status, preparation decisions and unresolved questions. The user decides what may leave the analysis account and manually transfers the approved summary into this repository.

## Acceptance criteria

- [ ] Read and use the `$wizard` skill when implementing. Preserve its template library and author only the task stages. Provide focused instructions, progress estimates, confirmation gates and a closing summary; make the wizard executable.
- [ ] Before authoring, make each stage's captured values, evidence sources, destinations and private/releasable classification concrete with the user. Provide verifiable commands or manual instructions; do not invent an unknown native format, interface or tool capability.
- [ ] Bash orchestrates the human procedure; all data-inspection computations run in Python. The user alone executes real-data commands in the analysis account; no agent runs there. The agent never opens private inputs or private evidence artifacts.
- [ ] Keep private working evidence separate from the proposed release summary. Do not automatically transfer, commit or upload evidence. Exclude participant values, record excerpts, private paths, raw logs, private contracts/reports, individual predictions and fitted models from the released material. Include only user-approved format/schema facts, conventions and aggregate checks needed by later tickets.
- [ ] Preserve the distinction between confirmed facts, documentary expectations, automated observations and unresolved assumptions. Unexpected codes or conflicts remain actionable findings rather than being silently repaired. No benchmark fitting is required for this ticket.
- [ ] Run Bash syntax validation and ShellCheck when available; statically trace captured values to their intended destinations. Verify Python inspection and summary-generation behaviour with invented fixtures only, including malformed/unsupported inputs and omission of record values from the proposed summary. Do not run the interactive wizard end to end as an agent.
- [ ] Supply clear private-execution, review and transfer instructions. The user runs the wizard, reviews the summary and transfers the approved evidence into this repository. Link that evidence from this ticket when completing it; script creation alone does not complete the ticket.
- [ ] The evidence gives Ticket 02 a reviewed basis for its input contract and preparation guidance. Any unresolved matter that prevents implementing that contract remains an explicit blocker requiring a user decision; no actual-input fact is inferred from invented-fixture tests.

## Execution boundary

This is a human-in-the-loop ticket with agent-authored tooling. Publication does not authorize implementation: implementation remains deferred. Source, documentation and invented fixtures are the only development inputs; instructions and Git ignores do not enforce access controls.
