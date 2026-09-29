> Invented teaching demonstration only. Generated with `examples/write_invented_inputs.py` and ahri-va 0.5.0; these are not participant findings.

# Adult InterVA5 replication benchmark

Agreement measures replication of InterVA5 assignments among eligible labelled adults in retained classes.
It does not establish accuracy against independently determined causes of death or performance across all adult causes.
Population: deaths aged 18 or older in the documented 2000–2024 study period; children, excluded causes and future deployment are outside this experiment.

Training-selected learner: **Logistic regression** (mean development CV exact-match agreement).

## Held-out agreement

| Model | Mean development CV agreement | Test exact-match agreement | Test macro F1 |
| --- | ---: | ---: | ---: |
| Most-frequent training label | 25.00% | 33.33% | 0.1667 |
| Logistic regression | 25.00% | 33.33% | 0.1667 |
| Random forest | 25.00% | 33.33% | 0.1667 |

Each fold uses only its training labels. The final baseline uses the full development portion.
Equal training counts select the lexicographically first exact label. The holdout is used only for final evaluation.
Macro F1 weights retained classes equally; a supported class with no correct predictions contributes zero.

## Development selection

Selected logistic-regression C: 0.1; chosen using mean development CV exact-match agreement only.
Equal scores favour the smaller C (stronger regularisation), larger forest leaves, and logistic regression between learners. All three models use the same development folds and final test records.
Settings and learner selection use development records only. Test results cannot change the selected learner, settings or protocol.

| C | Mean development CV agreement |
| ---: | ---: |
| 0.1 | 25.00% |
| 1 | 25.00% |
| 10 | 25.00% |

Selected random-forest minimum leaf size: 5; 200 trees.

| Minimum leaf size | Mean development CV agreement |
| ---: | ---: |
| 1 | 25.00% |
| 5 | 25.00% |

## Per-cause test recovery

Recall is the fraction of a cause's test records recovered by the training-selected learner: Logistic regression.
Excluded classes are not evaluated; no test support means not estimable, not zero recall.
Every retained class has test support; small counts do not establish reliable cause-specific performance.

| Class | Test support | Selected-learner recall |
| --- | ---: | ---: |
| <code>&#34;Invented cause A&#34;</code> | 1 | 100.00% |
| <code>&#34;Invented cause B&#34;</code> | 1 | 0.00% |
| <code>&#34;Invented rare cause&#34;</code> | 0 | not estimable (excluded) |
| <code>&#34;Undetermined&#34;</code> | 1 | 0.00% |

### Frequent confusions of the selected learner

Up to three directed confusion pairs with at least two test records, ordered by count then exact labels.
These are disagreements with recorded InterVA5 labels, not independently verified diagnostic errors.

No repeated confusion pair (at least two test records).

## Inclusion and exclusion

| Input | Rows | Missing identifiers | Unmatched | Matched |
| --- | ---: | ---: | ---: | ---: |
| deaths | 26 | 1 | 1 | 24 |
| indicators | 26 | 1 | 1 | 24 |

Among matched records, exclusions apply sequentially in this order:

| Stage | Excluded | Remaining |
| --- | ---: | ---: |
| missing age | 1 | 23 |
| invalid age | 1 | 22 |
| under 18 | 1 | 21 |
| missing target | 1 | 20 |
| unusable target | 1 | 19 |
| Classes with fewer than five eligible adults | 4 | 15 |

Retained coverage: 15 / 19 (78.95%) otherwise eligible labelled adults.
An empty denominator is not estimable and cannot produce a successful benchmark.

### Excluded exact classes

| Excluded class | Eligible count |
| --- | ---: |
| <code>&#34;Invented rare cause&#34;</code> | 4 |

### Retained exact classes

| Class | Eligible count | Development | Test |
| --- | ---: | ---: | ---: |
| <code>&#34;Invented cause A&#34;</code> | 5 | 4 | 1 |
| <code>&#34;Invented cause B&#34;</code> | 5 | 4 | 1 |
| <code>&#34;Undetermined&#34;</code> | 5 | 4 | 1 |

## Reproducibility

Seed: 42. Fixed cutoff: five eligible labelled adults per exact class.
Stratified development/test split: 12 / 3 records (requested 80/20).
Three stratified development folds, shuffled with seed 42; all class-coverage checks passed.
Same input order and package versions are required to reproduce record membership.

| Fold | Training | Validation | Baseline agreement | Logistic agreement | Forest agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 4 | 25.00% | 25.00% | 25.00% |
| 2 | 8 | 4 | 25.00% | 25.00% | 25.00% |
| 3 | 8 | 4 | 25.00% | 25.00% | 25.00% |

Baseline setting: `DummyClassifier(strategy="most_frequent")`; no tuning, weighting or resampling.
Logistic regression: L2 regularisation, lbfgs solver, multinomial loss for three or more classes (binary logistic loss for two).
Maximum iterations: 1000; tolerance: 0.0001; random_state: 42; no weighting or resampling.
Random forest: 200 trees; gini criterion; max_features=sqrt; unlimited depth; bootstrap=False; random_state=42; n_jobs=1; no weighting or resampling.
Encoding: all 353 allowlisted indicators; explicit y, n and - (missing/inapplicable) one-hot categories, with none dropped.
Each fold fits a fresh encoding/classifier pipeline on its training portion only; each learner's chosen pipeline is refit on full development.

| Package | Version |
| --- | --- |
| Python | 3.14.6 |
| ahri-va | 0.5.0 |
| scikit-learn | 1.8.0 |
| numpy | 2.4.3 |
| scipy | 1.17.1 |
| joblib | 1.5.3 |
| threadpoolctl | 3.6.0 |

Predictions and fitted models remain in memory; no individual-prediction or fitted-model files are produced.
Real-data reports remain in the analysis account until the user releases reviewed aggregates.
