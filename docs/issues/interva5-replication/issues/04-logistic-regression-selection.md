# 04 — Add training-only logistic-regression selection

Status: ready-for-agent
Progress: resolved

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** [03 — Run a baseline benchmark with population and partition checks](03-baseline-and-partition-checks.md).

**What to build:** Extend the working benchmark so it selects a regularised multinomial logistic-regression configuration using development records only, then reports that model's held-out replication agreement alongside the baseline. This is a complete, verifiable two-model milestone on the way to the approved three-model benchmark.

## Acceptance criteria

- [x] Compare exactly the three agreed regularisation strengths, `C = 0.1, 1, 10`, using mean exact-match agreement across the existing three development folds. Retain original class frequencies without weighting or resampling and use seed 42 for randomized steps.
- [x] Use the explicit indicator categories and predictor allowlist. Fit learned preprocessing within each training-only pipeline, including during cross-validation. No validation-fold or holdout information may fit preprocessing or influence tuning.
- [x] Choose the configuration using development cross-validation only; equal scores favour stronger regularisation. Refit the selected configuration on the full development portion and evaluate it on the same untouched test records as the baseline. Test results cannot change the selected configuration or protocol.
- [x] Extend the report with baseline and logistic-regression test agreement and macro F1, the chosen configuration and its development selection score, per-cause test support and logistic-regression recall, and updated reproducibility information. Label the report as an intermediate comparison until Ticket 05 adds the random forest and final learner selection.
- [x] Report absent support as not estimable rather than zero performance; successful accepted partitions still require support for every retained class. Keep interpretations restricted to replication and the retained benchmark population.
- [x] Failed fits or non-convergence stop successful completion with a clear diagnostic. A partial comparison must not appear to be a completed experiment. Keep predictions in memory and export no fitted models or individual predictions.
- [x] Verify through the command boundary using invented fixtures: the fixed tuning budget, shared partitions, category handling, deterministic tie-breaking, training-only preprocessing and held-out isolation. Perturbing held-out features must not change tuning or selected settings; perturbing excluded fields that do not affect eligibility/linkage must not change results.
- [x] Verify failed-fit/non-convergence outcomes, metric/report semantics, reproducible reruns and absence of prediction/model exports. Tests check protocol behaviour rather than demanding high agreement on invented records.

## Execution boundary

The user authorized Ticket 04 implementation on 29 September 2026. Use invented teaching fixtures exclusively for development and disposable test-model fitting. Only the user executes the benchmark on real records in the private analysis account.


## Completion record — 29 September 2026

Implemented the intermediate baseline/logistic-regression comparison in
`ahri-va benchmark`. Exactly C = 0.1, 1 and 10 are evaluated on the existing
three development folds. Fresh sparse one-hot/L2 logistic pipelines preserve
all three explicit indicator states and use only the 353 allowlisted predictors.
Selection uses unweighted mean fold agreement, with smaller C winning exact
ties. The chosen setting is refit on full development and evaluated on the same
test records as the baseline. There is no weighting, resampling or test-driven
reselection. `validate` continues to fit no models or preprocessing.

The aggregate Markdown report includes both models' test agreement and macro F1,
all candidate selection scores, chosen C, logistic per-cause test support and
recall, exclusion accounting and reproducibility settings. Excluded classes have
no test support and are marked not estimable. The report explicitly identifies
this as Ticket 04's intermediate comparison; random forests and final learner
selection remain for Ticket 05. Fits that fail or emit convergence warnings stop
with exit 2, value-free diagnostics and no partial report. Predictions and fitted
models remain in memory.

Verification on Python 3.14.6:

- **54 tests passed** in the full suite, including 17 benchmark command tests.
  Seven new tests cover all candidate settings and the ten-fit budget, common
  partitions, training-only preprocessing, explicit categories, deterministic
  default and nondefault ties, unequal fold sizes, worked metrics, absent
  support, failures/non-convergence, repeatability and absence of output files.
- Held-out feature perturbations leave all fitted inputs, coefficients and
  selected settings unchanged. Excluded-field perturbations leave the whole
  report unchanged. Reviewed blank mapping and undeclared-value rejection are
  exercised through `benchmark` as well as the existing validation tests.
- `mypy`: no issues in ten source files. Whitespace checks pass.
- Built `ahri_va-0.4.0-py3-none-any.whl` and installed it offline with pinned
  dependencies into a fresh environment outside the repository. Console and
  module entry points produced the same invented comparison without additional
  artifacts. The final reviewed wheel was reinstalled and checked. The constant
  invented example selects C = 0.1 at 25.00% mean CV agreement; both models have
  33.33% test agreement and 0.1667 macro F1. These are software checks only.
- **Standards review:** two low-severity comments (C naming and pure nested test
  helpers) fixed and independently rechecked; zero outstanding findings.
- **Specification review:** zero findings. Both reviews compared the scoped
  implementation with starting commit `eab18204f348991c684c85828f2d0aef59aed716`.

The [benchmark guide](../../../benchmark.md) documents use and offline transfer.
The ignored `dist/ticket04-wheelhouse/` contains the application and dependency
wheels for the verified Python 3.14/macOS ARM64 environment; other runtimes need
matching wheels. `dist/invented-ticket04-comparison.md` is an invented example
report. Runtime dependency pins and the input configuration are unchanged.

All development and disposable fitting used invented records only. No participant
records or private artifacts were inspected, and private-data feasibility remains
for user execution and review in the separate analysis account. Ticket 05 is now
dependency-unblocked and remains outside this implementation's scope.
