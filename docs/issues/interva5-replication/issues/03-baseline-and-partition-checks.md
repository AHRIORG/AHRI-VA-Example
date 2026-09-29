# 03 — Run a baseline benchmark with population and partition checks

Status: ready-for-agent
Progress: resolved

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** None — [Ticket 02](02-validate-inputs-and-adult-eligibility.md) is resolved.

**What to build:** A runnable `benchmark` command that turns validated eligible labelled adults into the agreed benchmark population, checks the shared holdout/development partitions and produces an interpretable most-frequent-training-label baseline report. Extend `validate` with the same population and partition-feasibility checks without fitting a model.

## Acceptance criteria

- [x] Both commands apply the same input and eligibility rules. After linkage and adult/target eligibility checks, count exact target classes and exclude every class with fewer than five eligible labelled adults, including an explicit undetermined class. Remove all records of excluded classes from training and evaluation; do not pool or relabel causes.
- [x] Report excluded classes and counts, sequential inclusion/exclusion counts, and the retained fraction of otherwise eligible labelled adults. An empty denominator is not estimable. Require at least two retained classes.
- [x] Generate one approximately 80/20 stratified development/test split with seed 42. Verify at least one test example and three development examples per retained class. Generate three stratified development folds once and verify every retained class appears in each training and validation portion.
- [x] Stop with a clear diagnostic on infeasible coverage. Do not retry seeds, adjust the five-record cutoff or silently alter the split/fold protocol. Make the same partitions available to the learners added by subsequent tickets.
- [x] Fit the most-frequent-label baseline using training labels only: each fold's training portion for cross-validation and the full development portion for final test evaluation. Keep the holdout separate from model development.
- [x] Produce a concise Markdown baseline report stating that agreement measures replication of InterVA5 assignments among eligible labelled adults in retained classes. Include test exact-match agreement as a percentage, macro F1, exclusions, retained coverage, seed, split/fold sizes and package versions. Identify this as the baseline milestone; completion of the full three-model comparison belongs to Ticket 05.
- [x] Keep intermediate predictions in memory and produce no individual-prediction or fitted-model files. Real-data reports remain in the analysis account until the user releases reviewed aggregates.
- [x] Verify through the public commands using invented fixtures: counts of four and five, undetermined subject to the same cutoff, a class falling below five only after eligibility checks, no eligible adults, no retained classes and one retained class. Check exclusion accounting and preservation of retained labels.
- [x] Verify valid partitions and failures despite the five-record cutoff, including inadequate test capacity and missing fold coverage. Check fixed-seed repeatability, holdout separation, training-derived baseline behaviour and no model fitting by `validate`. A complete invented-data run produces the expected baseline report without forbidden output artifacts.

## Execution boundary

The user authorized Ticket 03 implementation on 29 September 2026. All development runs and model fitting use invented teaching fixtures only. Private-data feasibility and real-data findings are not established by completing this ticket.


## Completion record — 29 September 2026

Implemented `ahri-va benchmark` and extended `ahri-va validate` with the shared
population and partition checks. Both commands preserve the reviewed input rules,
exclude exact classes below five after eligibility, and report reconcilable
counts and retained coverage. Empty coverage is not estimable; fewer than two
retained classes fails. An immutable in-memory partition plan uses seed 42 for
one stratified 80/20 split and three shuffled stratified development folds,
checking coverage and separation before fitting.

The baseline fits each fold's training labels and then the complete development
labels, with deterministic lexicographic tie-breaking. Its Markdown report on
stdout states the restricted replication objective and baseline milestone,
exclusions, coverage, agreement, macro F1, split/fold sizes and package versions.
No record membership, individual predictions or fitted models are exported.
The [baseline guide](../../../benchmark.md) covers installation, invented inputs,
report interpretation and offline transfer; the updated validation guide explains
the command's new feasibility requirement.

Verification on Python 3.14.6:

- Full suite: **47 tests passed**, including ten baseline/population command tests,
  the 23 retained input-contract tests and 14 evidence-tooling tests. All inputs
  were invented. The small Ticket 02 fixtures now check their original eligibility
  counts in the explicit population-failure summary.
- `mypy`: no issues in nine source files. Staged whitespace checks pass.
- Built `ahri_va-0.3.0-py3-none-any.whl`, collected all pinned runtime wheels and
  installed offline into a fresh environment outside the repository. The final
  wheel was reinstalled and verified after review. The invented example retained
  15 of 19 eligible adults and produced the expected 25.00% mean CV agreement,
  33.33% test agreement and 0.1667 test macro F1, with no extra output artifacts.
- Standards review: one Markdown-label rendering finding was fixed and independently
  rechecked with invented labels through a GFM renderer; zero outstanding findings.
  Specification review: zero actionable findings. Review compared Ticket 03 against
  the separate Ticket 02 prerequisite commit `fbfd14a`.

Runtime versions are pinned in `pyproject.toml`. The ignored
`dist/ticket03-wheelhouse/` contains the application and dependency wheels for the
verified Python 3.14/macOS ARM64 environment; other runtimes require matching
wheels. `dist/invented-ticket03-baseline.md` is an invented example report.

Only source, documentation and invented fixtures were used. No participant
records or private artifacts were inspected, and no private-data feasibility or
scientific finding is claimed. Ticket 04 is dependency-unblocked but remains
outside this authorization. The unrelated existing course-prompt edit is untouched.
