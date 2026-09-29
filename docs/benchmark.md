# Adult InterVA5 replication benchmark

This benchmark measures agreement with recorded InterVA5 first-cause assignments
among eligible labelled adults in retained classes. It is not validation against
independent reference causes. The completed comparison includes the most-frequent
training-label baseline, logistic regression and a random forest. The learner and
both settings are chosen using development data only; test scores are reporting
only. No minimum agreement is required.

## Install and run invented records

Use Python 3.11+ in a virtual environment. Runtime versions are pinned in
`pyproject.toml`: scikit-learn 1.8.0, NumPy 2.4.3, SciPy 1.17.1, joblib 1.5.3
and threadpoolctl 3.6.0. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m pip install --no-build-isolation '.[dev]'
python3 examples/write_invented_inputs.py --output-dir /tmp/ahri-va-invented-ticket05
.venv/bin/ahri-va validate \
  --deaths /tmp/ahri-va-invented-ticket05/deaths.csv \
  --indicators /tmp/ahri-va-invented-ticket05/indicators.csv \
  --config config/validation.example.json
.venv/bin/ahri-va benchmark \
  --deaths /tmp/ahri-va-invented-ticket05/deaths.csv \
  --indicators /tmp/ahri-va-invented-ticket05/indicators.csv \
  --config config/validation.example.json
```

Choose a new fixture directory; the generator refuses to overwrite one. The
equivalent module entry point is `.venv/bin/python -m ahri_va`. Success exits 0.
`validate` prints aggregate JSON without fitting; `benchmark` prints Markdown
to stdout. Redirect benchmark stdout to a chosen `.md` path to save the report.
The shell can create an empty file on failure, so always check the exit code.
Errors exit 2 and print JSON to stderr without a partial report.

The example has 26 rows per input, 24 matched records, five sequential eligibility
exclusions and 19 eligible labelled adults. One four-record class is removed,
retaining 15/19 (78.95%). Three five-record classes each supply four development
and one test record. Each development fold has eight training and four validation
records. Expected baseline mean CV agreement is 25.00%, test agreement 33.33%,
and test macro F1 0.1667. The constant-feature logistic candidates tie at 25.00%
mean CV agreement, choosing C = 0.1; test agreement is 33.33% and macro F1
0.1667. Both 200-tree forest settings also tie at 25.00% CV agreement, choosing
minimum leaf size 5, with test agreement 33.33% and macro F1 0.1667. Logistic
regression wins the between-learner tie. This intentionally weak example tests
software behaviour only; it is not a scientific result. See the saved
[invented demonstration report](../examples/invented-benchmark.md).

## Population and protocol

Both commands use the [reviewed input contract](validation.md) and unchanged
[configuration template](../config/validation.example.json). After linkage and
adult/target eligibility, count exact target labels. Exclude all records in each
class with fewer than five eligible adults, including `Undetermined`; never pool
or relabel classes. Retained coverage divides retained records by all otherwise
eligible labelled adults. A zero denominator is not estimable (`null` in JSON).
Fewer than two retained classes stops either command.

Use [scikit-learn's stratified split](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.train_test_split.html)
with test size 0.2 and seed 42 (test size rounds up). Require at least one test
and three development records per retained class. Generate three
[stratified development folds](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.StratifiedKFold.html)
with shuffling and seed 42. Every training/validation portion must cover every
retained class. The implementation also verifies disjoint, exhaustive partitions
and that each development record is validated exactly once. Coverage failures
stop with no seed retries or changes to cutoff, test fraction or fold count.

The immutable `PartitionPlan` in `src/ahri_va/partitions.py` is built once per
command. Development, test and fold indices all refer to retained population
rows in deaths-file order. All three models reuse that plan. Input order and
the recorded package versions are part of reproducibility; row membership is
never exported.

The [most-frequent baseline](https://scikit-learn.org/1.8/modules/generated/sklearn.dummy.DummyClassifier.html)
fits each fold's training labels, then fits the full development labels for test
evaluation. Equal training counts choose the lexicographically first exact label.
It ignores predictor values. CV agreement is the unweighted mean of the three
fold agreements. Test exact-match agreement is a percentage; macro F1 gives each
retained class equal weight. All accepted partitions have support for every
retained class. A supported class with no correct predictions has F1 zero.

The [logistic-regression learner](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html)
uses L2 regularisation (`l1_ratio=0`), the lbfgs solver, a 1000-iteration limit,
tolerance 0.0001 and seed 42. For three or more retained classes, this solver
fits the multinomial loss; for two classes it uses binary logistic loss.
Exactly C = 0.1, 1 and 10 are compared on the shared three folds. Select the
largest unweighted mean fold agreement; exact ties favour smaller C. There is
no class weighting or resampling, and macro F1 does not influence selection.
Refit the chosen setting on all development records and evaluate it once on the
same test records as the baseline and forest. Test results cannot change that choice.

The random forest compares exactly 200 trees with minimum leaf sizes 1 and 5.
It uses seed 42, Gini splits, square-root feature sampling, unlimited depth and
a single worker. `bootstrap=False` ensures every tree receives the original
training rows without resampling; class weights and sample weights are absent.
The larger leaf size wins exact CV ties. Choose between the two selected
settings by unweighted mean CV agreement, with logistic regression winning exact
between-learner ties. Selection finishes before either learner is scored on the
holdout. This is exactly five configurations, not a tunable search interface.

Each fit uses a fresh pipeline with a sparse
[one-hot encoder](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.OneHotEncoder.html)
for all 353 allowlisted indicators. Every indicator has explicit `y`, `n`, `-`
categories with none dropped; `-` stays distinct as missing/inapplicable.
Categories come from the input contract. Fitting sees only the fold's training
records (or full development for the final refit), even when a category occurs
only in held-out records. Validation still rejects undeclared values and blanks
without the explicitly reviewed mapping. No other fields become predictors.

Failed fitting or scoring and any convergence warning stop the command with
exit 2 and a value-free diagnostic; no partial comparison is printed. There
are no retries, candidate skipping or automatic changes to solver settings.
All 15 candidate-fold fits and both selected refits must succeed, as must the
baseline fits. Weak agreement is a valid result when the protocol completes.

The report includes sequential counts, excluded and retained exact class counts,
retained coverage, split/fold sizes, metrics, fixed settings and installed package
versions. It shows all five candidate CV scores, the chosen C and leaf size,
and each model's held-out exact-match agreement and macro F1. The training-selected
learner is clearly named above the comparison. Per-cause recall describes that
selected learner even if another model has better test agreement. A supported
class with no recovered test records has zero recall; excluded classes have zero test support and are marked
not estimable. Labels are quoted and escaped for Markdown without changing the labels
used by the experiment. At most three repeated directed confusion pairs are
listed, requiring at least two test records per pair and breaking count ties
by exact labels. These describe disagreements with InterVA5, not verified
diagnostic errors; there is no default confusion matrix. Diagnostics omit paths
and record values; aggregate class summaries intentionally include the exact labels.

## Development verification

```bash
.venv/bin/python -m mypy
.venv/bin/python -m unittest discover -s tests -p test_benchmark.py -v
.venv/bin/python -m unittest discover -s tests -v
```

Tests invoke the public commands with invented temporary CSVs and configuration.
They cover rare-class accounting, exact labels, empty/single-class failures,
partition coverage, repeatability, training-only fitting, report metrics and
absence of output artifacts. Learner checks observe external scikit-learn
boundaries to verify the exact fit budget, common partitions, explicit categories
and training-only fitting. Held-out feature perturbations leave every fitted
input, fitted coefficients/trees and selected settings/learner unchanged.
Excluded-field perturbations leave the report unchanged. Controlled predictions verify unweighted fold
selection and nondefault ties, poor test scores without reselection, worked
metrics, selected-learner confusion counts and absent support. Failures and
convergence warnings are injected at initial/later candidates and the final refit.
External splitter fault injection exercises guard failures that the normal five-record cutoff would generally prevent. The older
small eligibility fixtures now assert population failures while checking their
original eligibility counts in the aggregate failure summary.

## Private preparation and review

Only the user performs these steps in the separate analysis account:

1. Use [Ticket 01's approved evidence](issues/interva5-replication/reviewed-input-evidence.md)
   and its [completion record](issues/interva5-replication/issues/01-private-input-evidence-wizard.md#completion-record--29-september-2026)
   to check the current export. The reviewed v2 inputs are UTF-8 CSVs, need no
   conversion, preserve original identifiers, use completed age at death, declare
   `[""]` missing tokens and use the exact label `Undetermined`.
2. Start from [validation.example.json](../config/validation.example.json), with
   the [configuration rules](validation.md#reviewed-input-contract). Keep exact
   identifiers and labels. The existing no-blank observation does not define any
   future blank's meaning: blanks remain rejected unless a new mapping to `-`
   is privately reviewed and explicitly declared. New tokens, exports, schema
   changes and semantic changes need private review; the software cannot infer
   them or establish actual-input validity from invented fixtures.
3. Run `validate` with private paths and check exit 0, reconcilable exclusions,
   excluded classes, retained coverage and fold coverage. A feasible split does
   not guarantee reliable uncommon-cause estimates. Do not adjust the seed,
   cutoff or budget in response to benchmark performance.
4. Run `benchmark` with the same paths and reviewed configuration. Save stdout
   to a private Markdown file and check exit 0 before treating it as complete.
   Inspect the three rows, training-selected marker, support, recall and confusion
   counts. The report describes eligible labelled adults in retained classes
   from the documented study period; it does not establish independent cause
   accuracy, performance for excluded causes, or future deployment validity.
5. Keep inputs, diagnostics and the report private. Review exact cause labels,
   small counts and all aggregates before deciding what is suitable to release.
   No private outputs or logs are needed by the development account or an agent.

The reviewed evidence applies to the user-reviewed exports. Current private-data
feasibility, any changed input facts, and scientific interpretation remain the
user's responsibility. Documentation, configuration declarations and Git ignores
are not access controls.

## Offline transfer

Build from a clean source checkout on a machine matching the destination Python
version, OS and architecture. A clean checkout avoids obsolete files left in a
previous setuptools build directory:

```bash
.venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index . --wheel-dir dist
.venv/bin/python -m pip download --only-binary=:all: \
  --dest dist/ticket05-wheelhouse dist/ahri_va-0.5.0-py3-none-any.whl
```

Transfer the wheelhouse, configuration template and guides. In a destination
virtual environment, install without contacting a package index:

```bash
python -m pip install --no-index --find-links /path/to/ticket05-wheelhouse ahri-va==0.5.0
```

The application wheel alone no longer suffices: the numerical libraries require
compatible wheels. Do not copy the development virtual environment across
accounts. The Ticket 01 archive builder remains specific to evidence tooling.

Only the user runs real-data commands in the separate analysis account. Real-data
reports remain there until the user releases reviewed aggregates. Intermediate
predictions and fitted models stay in memory; neither command writes individual
predictions, models or partition membership. No private-data feasibility or
scientific findings follow from the invented examples. Instructions and Git
ignores do not enforce access controls.
