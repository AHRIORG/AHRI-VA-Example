# Baseline benchmark (Ticket 03)

This milestone measures agreement with recorded InterVA5 first-cause assignments
among eligible labelled adults in retained classes. It is not validation against
independent reference causes. Ticket 05 completes the three-model comparison;
this version evaluates only the most-frequent-training-label baseline.

## Install and run invented records

Use Python 3.11+ in a virtual environment. Runtime versions are pinned in
`pyproject.toml`: scikit-learn 1.8.0, NumPy 2.4.3, SciPy 1.17.1, joblib 1.5.3
and threadpoolctl 3.6.0. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m pip install --no-build-isolation '.[dev]'
python3 examples/write_invented_inputs.py --output-dir /tmp/ahri-va-invented-ticket03
.venv/bin/ahri-va validate \
  --deaths /tmp/ahri-va-invented-ticket03/deaths.csv \
  --indicators /tmp/ahri-va-invented-ticket03/indicators.csv \
  --config config/validation.example.json
.venv/bin/ahri-va benchmark \
  --deaths /tmp/ahri-va-invented-ticket03/deaths.csv \
  --indicators /tmp/ahri-va-invented-ticket03/indicators.csv \
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
and test macro F1 0.1667. These invented results test software behaviour only.

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
rows in deaths-file order. Later learners must reuse that plan. Input order and
the recorded package versions are part of reproducibility; row membership is
never exported.

The [most-frequent baseline](https://scikit-learn.org/1.8/modules/generated/sklearn.dummy.DummyClassifier.html)
fits each fold's training labels, then fits the full development labels for test
evaluation. Equal training counts choose the lexicographically first exact label.
It ignores predictor values. CV agreement is the unweighted mean of the three
fold agreements. Test exact-match agreement is a percentage; macro F1 gives each
retained class equal weight. All accepted partitions have support for every
retained class. A supported class with no correct predictions has F1 zero.

The report includes sequential counts, excluded and retained exact class counts,
retained coverage, split/fold sizes, metrics, fixed settings and installed package
versions. Labels are quoted and escaped for Markdown without changing the labels
used by the experiment. Diagnostics omit paths and record values; aggregate
class summaries intentionally include the exact labels.

## Development verification

```bash
.venv/bin/python -m mypy
.venv/bin/python -m unittest discover -s tests -p test_benchmark.py -v
.venv/bin/python -m unittest discover -s tests -v
```

Tests invoke the public commands with invented temporary CSVs and configuration.
They cover rare-class accounting, exact labels, empty/single-class failures,
partition coverage, repeatability, training-only fitting, report metrics and
absence of output artifacts. External splitter fault injection exercises guard
failures that the normal five-record cutoff would generally prevent. The older
small eligibility fixtures now assert population failures while checking their
original eligibility counts in the aggregate failure summary.

## Offline transfer

Build on a machine matching the destination Python version, OS and architecture:

```bash
.venv/bin/python -m pip wheel --no-build-isolation --no-deps --no-index . --wheel-dir dist
.venv/bin/python -m pip download --only-binary=:all: \
  --dest dist/ticket03-wheelhouse dist/ahri_va-0.3.0-py3-none-any.whl
```

Transfer the wheelhouse, configuration template and guides. In a destination
virtual environment, install without contacting a package index:

```bash
python -m pip install --no-index --find-links /path/to/ticket03-wheelhouse ahri-va==0.3.0
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
