# 05 — Complete the random-forest comparison and benchmark report

Status: ready-for-agent
Progress: resolved

**Parent:** [Adult InterVA5 first-cause replication benchmark](../spec.md)

**Blocked by:** [04 — Add training-only logistic-regression selection](04-logistic-regression-selection.md).

**What to build:** Complete the agreed benchmark by adding the limited random-forest comparison, choosing the learner using training-only cross-validation and producing the final concise three-model report. Deliver an invented-data demonstration and the usage guidance needed for the user to execute and review the benchmark privately.

## Acceptance criteria

- [x] Compare random forests with 200 trees and minimum leaf sizes of 1 or 5. Together with the three logistic-regression configurations, this is exactly the agreed five-configuration tuning budget. Use seed 42 for randomized steps, retain original class frequencies and perform no weighting or resampling.
- [x] All configurations use the same development folds, predictor allowlist and training-only preprocessing rules. Select each learner's setting and the overall learner by mean cross-validation exact-match agreement using development records only. Ties favour logistic regression between learners, stronger regularisation within logistic regression, and the larger leaf size within random forests.
- [x] Fit each learner at its chosen setting and the most-frequent-label baseline on the full development portion. Evaluate all three on the same final test records. Mark the learner selected by development cross-validation; test scores cannot select a different winner, setting or protocol.
- [x] Reject failed fits, non-convergence and infeasible coverage without reporting a partial experiment as completed. No minimum agreement threshold is required for a technically valid benchmark.
- [x] Produce one concise Markdown report with the replication objective and population limits; reconcilable inclusion/exclusion counts; excluded rare classes and counts; retained fraction; three model rows with test agreement percentages and macro F1; and the training-selected learner clearly marked.
- [x] Include per-cause test support and recall percentages for the selected learner, marking absent support as not estimable. Explain frequent cause confusions concisely when useful without a large default matrix. Include seed, split/fold sizes, chosen settings and package versions in a short reproducibility appendix.
- [x] Preserve the agreed artifact boundary: intermediate predictions stay in memory; no individual predictions or fitted models are exported. The private report remains in the analysis account until the user decides which reviewed aggregates to release.
- [x] Complete the configuration guidance, invented examples, pinned dependencies and concise instructions for installation, `validate`, `benchmark`, private preparation using Ticket 01's evidence, and user review of outputs. Unresolved private facts remain explicit; documentation and Git ignores are not presented as access controls.
- [x] Run appropriate command-boundary verification and an installed-package smoke check using invented inputs only. Cover the full five-configuration budget, shared folds/test records, deterministic selection and ties, holdout isolation, predictor exclusions, fit failures, report metrics and population limits, and absence of forbidden artifacts. Retain the validation, eligibility and feasibility coverage from earlier tickets.
- [x] A complete invented-data benchmark produces the final three-model report and passes the accepted protocol checks. This establishes software acceptance only; private-data execution, feasibility and scientific findings remain the user's responsibility.

## Execution boundary

The user authorized Ticket 05 implementation on 29 September 2026. Development uses source, documentation, the reviewed evidence handoff and invented fixtures only. No agent runs in the private analysis account, and no real-data artifact is used for development tests.


## Completion record — 29 September 2026

Implemented the complete three-model `ahri-va benchmark` report in version
0.5.0. The fixed budget is C = 0.1, 1, 10 and 200-tree forests with minimum
leaf sizes 1 and 5. All five settings reuse the same three development folds,
353-indicator allowlist and fresh training-only encoding pipelines. Forest
bootstrapping is disabled so no training records are resampled; neither learner
uses class or sample weighting. Seed 42 is retained throughout.

Both settings and the overall learner are selected before either learner sees
the holdout. Exact ties favour smaller C, larger leaf size and logistic
regression between learners. Each learner is refit on full development and
reported beside the most-frequent-label baseline on the same final test records.
Failed fitting/scoring or convergence warnings abort with value-free diagnostics
and no partial report. Weak agreement remains a valid software outcome.

The final report marks the training-selected learner, includes its per-cause
support/recall and up to three repeated directed confusions, and retains
reconcilable exclusion counts, excluded classes, retained fraction, population
limits, split/fold sizes, settings and package versions. Intermediate predictions
and fitted models remain in memory. The unchanged configuration template and
updated [benchmark guide](../../../benchmark.md) cover installation, both commands,
private preparation from Ticket 01's reviewed evidence, output review and offline
transfer. Changed private input facts and scientific findings remain unresolved
until user review; instructions and Git ignores are not access controls.

Verification on Python 3.14.6:

- **57 tests passed** in the full suite, including 20 benchmark command tests.
  Coverage retains earlier input/eligibility/feasibility checks and adds forest
  ties, training-selected diagnostics despite better competing test scores,
  repeated confusion counts, all 15 candidate-fold fits and two refits, shared
  folds/test records, no weighting/resampling, and forest failures at initial
  candidates, later candidates, refit and prediction.
- Held-out feature changes leave both learners' fitted inputs, fitted parameters,
  CV settings and selected learner unchanged. Excluded-field changes preserve the
  whole report; repeated runs are deterministic. Commands produce no forbidden
  output files.
- `mypy`: no issues in ten source files. Scoped whitespace checks pass.
- Built the wheel from a clean source staging directory, verifying it contains
  the predictor allowlist and no obsolete logistic-only module. Installed offline
  with all pinned dependencies into a fresh environment outside the repository.
  Console and module entry points produced identical invented reports;
  `validate` fitted no models, and no output artifacts were created by commands.
- The [invented demonstration](../../../../examples/invented-benchmark.md)
  retains 15/19 eligible adults (78.95%). All three models have 33.33% test
  agreement and 0.1667 macro F1. The CV ties select C = 0.1, leaf size 5 and
  logistic regression. These are invented software checks, not scientific results.

The ignored `dist/ticket05-wheelhouse/` holds the application wheel and dependencies
for the verified Python 3.14/macOS ARM64 runtime; other destination runtimes need
matching wheels. The checked-in invented demonstration is reproducible with the
existing fixture generator. All development and disposable fitting used invented
records only. No participant records or private artifacts were inspected.

Independent two-axis code review compared the scoped implementation with starting
commit `6c77f80bd1c294f455f9b610129ddffaf7a8be00`:

- **Standards:** zero hard violations and zero actionable smell findings. The
  temporary completion-record staging note was resolved and rechecked.
- **Spec:** zero missing/incorrect requirements or unrequested scope additions.
  The final invented demonstration and packaging evidence were rechecked.

All Ticket 05 acceptance criteria are complete. Private-data execution, feasibility
and scientific findings remain the user's responsibility in the analysis account.
