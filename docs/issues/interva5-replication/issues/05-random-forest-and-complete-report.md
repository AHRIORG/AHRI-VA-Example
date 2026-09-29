# 05 — Complete the random-forest comparison and benchmark report

Status: ready-for-agent

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** [04 — Add training-only logistic-regression selection](04-logistic-regression-selection.md).

**What to build:** Complete the agreed benchmark by adding the limited random-forest comparison, choosing the learner using training-only cross-validation and producing the final concise three-model report. Deliver an invented-data demonstration and the usage guidance needed for the user to execute and review the benchmark privately.

## Acceptance criteria

- [ ] Compare random forests with 200 trees and minimum leaf sizes of 1 or 5. Together with the three logistic-regression configurations, this is exactly the agreed five-configuration tuning budget. Use seed 42 for randomized steps, retain original class frequencies and perform no weighting or resampling.
- [ ] All configurations use the same development folds, predictor allowlist and training-only preprocessing rules. Select each learner's setting and the overall learner by mean cross-validation exact-match agreement using development records only. Ties favour logistic regression between learners, stronger regularisation within logistic regression, and the larger leaf size within random forests.
- [ ] Fit each learner at its chosen setting and the most-frequent-label baseline on the full development portion. Evaluate all three on the same final test records. Mark the learner selected by development cross-validation; test scores cannot select a different winner, setting or protocol.
- [ ] Reject failed fits, non-convergence and infeasible coverage without reporting a partial experiment as completed. No minimum agreement threshold is required for a technically valid benchmark.
- [ ] Produce one concise Markdown report with the replication objective and population limits; reconcilable inclusion/exclusion counts; excluded rare classes and counts; retained fraction; three model rows with test agreement percentages and macro F1; and the training-selected learner clearly marked.
- [ ] Include per-cause test support and recall percentages for the selected learner, marking absent support as not estimable. Explain frequent cause confusions concisely when useful without a large default matrix. Include seed, split/fold sizes, chosen settings and package versions in a short reproducibility appendix.
- [ ] Preserve the agreed artifact boundary: intermediate predictions stay in memory; no individual predictions or fitted models are exported. The private report remains in the analysis account until the user decides which reviewed aggregates to release.
- [ ] Complete the configuration guidance, invented examples, pinned dependencies and concise instructions for installation, `validate`, `benchmark`, private preparation using Ticket 01's evidence, and user review of outputs. Unresolved private facts remain explicit; documentation and Git ignores are not presented as access controls.
- [ ] Run appropriate command-boundary verification and an installed-package smoke check using invented inputs only. Cover the full five-configuration budget, shared folds/test records, deterministic selection and ties, holdout isolation, predictor exclusions, fit failures, report metrics and population limits, and absence of forbidden artifacts. Retain the validation, eligibility and feasibility coverage from earlier tickets.
- [ ] A complete invented-data benchmark produces the final three-model report and passes the accepted protocol checks. This establishes software acceptance only; private-data execution, feasibility and scientific findings remain the user's responsibility.

## Execution boundary

Implementation remains deferred until authorized. Development uses source, documentation, the reviewed evidence handoff and invented fixtures only. No agent runs in the private analysis account, and no real-data artifact is used for development tests.
