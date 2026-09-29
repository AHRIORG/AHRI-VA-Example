# 03 — Run a baseline benchmark with population and partition checks

Status: ready-for-agent

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** [02 — Validate inputs and identify eligible labelled adults](02-validate-inputs-and-adult-eligibility.md).

**What to build:** A runnable `benchmark` command that turns validated eligible labelled adults into the agreed benchmark population, checks the shared holdout/development partitions and produces an interpretable most-frequent-training-label baseline report. Extend `validate` with the same population and partition-feasibility checks without fitting a model.

## Acceptance criteria

- [ ] Both commands apply the same input and eligibility rules. After linkage and adult/target eligibility checks, count exact target classes and exclude every class with fewer than five eligible labelled adults, including an explicit undetermined class. Remove all records of excluded classes from training and evaluation; do not pool or relabel causes.
- [ ] Report excluded classes and counts, sequential inclusion/exclusion counts, and the retained fraction of otherwise eligible labelled adults. An empty denominator is not estimable. Require at least two retained classes.
- [ ] Generate one approximately 80/20 stratified development/test split with seed 42. Verify at least one test example and three development examples per retained class. Generate three stratified development folds once and verify every retained class appears in each training and validation portion.
- [ ] Stop with a clear diagnostic on infeasible coverage. Do not retry seeds, adjust the five-record cutoff or silently alter the split/fold protocol. Make the same partitions available to the learners added by subsequent tickets.
- [ ] Fit the most-frequent-label baseline using training labels only: each fold's training portion for cross-validation and the full development portion for final test evaluation. Keep the holdout separate from model development.
- [ ] Produce a concise Markdown baseline report stating that agreement measures replication of InterVA5 assignments among eligible labelled adults in retained classes. Include test exact-match agreement as a percentage, macro F1, exclusions, retained coverage, seed, split/fold sizes and package versions. Identify this as the baseline milestone; completion of the full three-model comparison belongs to Ticket 05.
- [ ] Keep intermediate predictions in memory and produce no individual-prediction or fitted-model files. Real-data reports remain in the analysis account until the user releases reviewed aggregates.
- [ ] Verify through the public commands using invented fixtures: counts of four and five, undetermined subject to the same cutoff, a class falling below five only after eligibility checks, no eligible adults, no retained classes and one retained class. Check exclusion accounting and preservation of retained labels.
- [ ] Verify valid partitions and failures despite the five-record cutoff, including inadequate test capacity and missing fold coverage. Check fixed-seed repeatability, holdout separation, training-derived baseline behaviour and no model fitting by `validate`. A complete invented-data run produces the expected baseline report without forbidden output artifacts.

## Execution boundary

Implementation remains deferred until authorized. All development runs and model fitting use invented teaching fixtures only. Private-data feasibility and real-data findings are not established by completing this ticket.
