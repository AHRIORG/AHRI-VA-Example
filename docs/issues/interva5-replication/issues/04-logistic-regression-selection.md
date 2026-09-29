# 04 — Add training-only logistic-regression selection

Status: ready-for-agent

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** [03 — Run a baseline benchmark with population and partition checks](03-baseline-and-partition-checks.md).

**What to build:** Extend the working benchmark so it selects a regularised multinomial logistic-regression configuration using development records only, then reports that model's held-out replication agreement alongside the baseline. This is a complete, verifiable two-model milestone on the way to the approved three-model benchmark.

## Acceptance criteria

- [ ] Compare exactly the three agreed regularisation strengths, `C = 0.1, 1, 10`, using mean exact-match agreement across the existing three development folds. Retain original class frequencies without weighting or resampling and use seed 42 for randomized steps.
- [ ] Use the explicit indicator categories and predictor allowlist. Fit learned preprocessing within each training-only pipeline, including during cross-validation. No validation-fold or holdout information may fit preprocessing or influence tuning.
- [ ] Choose the configuration using development cross-validation only; equal scores favour stronger regularisation. Refit the selected configuration on the full development portion and evaluate it on the same untouched test records as the baseline. Test results cannot change the selected configuration or protocol.
- [ ] Extend the report with baseline and logistic-regression test agreement and macro F1, the chosen configuration and its development selection score, per-cause test support and logistic-regression recall, and updated reproducibility information. Label the report as an intermediate comparison until Ticket 05 adds the random forest and final learner selection.
- [ ] Report absent support as not estimable rather than zero performance; successful accepted partitions still require support for every retained class. Keep interpretations restricted to replication and the retained benchmark population.
- [ ] Failed fits or non-convergence stop successful completion with a clear diagnostic. A partial comparison must not appear to be a completed experiment. Keep predictions in memory and export no fitted models or individual predictions.
- [ ] Verify through the command boundary using invented fixtures: the fixed tuning budget, shared partitions, category handling, deterministic tie-breaking, training-only preprocessing and held-out isolation. Perturbing held-out features must not change tuning or selected settings; perturbing excluded fields that do not affect eligibility/linkage must not change results.
- [ ] Verify failed-fit/non-convergence outcomes, metric/report semantics, reproducible reruns and absence of prediction/model exports. Tests check protocol behaviour rather than demanding high agreement on invented records.

## Execution boundary

Implementation remains deferred until authorized. Use invented teaching fixtures exclusively for development and disposable test-model fitting. Only the user executes the benchmark on real records in the private analysis account.
