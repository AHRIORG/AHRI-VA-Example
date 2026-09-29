"""Training-only logistic-regression tuning over the shared partition plan."""

from dataclasses import dataclass
from statistics import mean
import warnings

from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ahri_va.baseline import Scores
from ahri_va.config import ValidationError
from ahri_va.partitions import PartitionPlan, SEED
from ahri_va.population import BenchmarkPopulation
from ahri_va.validation import PREDICTORS


__all__ = ["CandidateResult", "CauseRecall", "LogisticResult", "evaluate_logistic"]

C_VALUES = (0.1, 1.0, 10.0)
MAX_ITERATIONS = 1000
TOLERANCE = 1e-4


@dataclass(frozen=True)
class CandidateResult:
    """One fixed C and its three development-fold scores."""

    regularisation_c: float
    folds: tuple[Scores, ...]

    @property
    def mean_cv_agreement(self) -> float:
        """Return the unweighted mean exact-match agreement across folds."""
        return mean(score.agreement for score in self.folds)


@dataclass(frozen=True)
class CauseRecall:
    """Test support and recall; absent support is explicitly not estimable."""

    support: int
    recall: float | None


@dataclass(frozen=True)
class LogisticResult:
    """Aggregate tuning and test results; no predictions or fitted models."""

    candidates: tuple[CandidateResult, ...]
    selected: CandidateResult
    test: Scores
    per_cause: dict[str, CauseRecall]


def _pipeline(regularisation_c: float) -> Pipeline:
    # Categories come from the accepted input contract, never from held-out
    # records. Keeping all three columns preserves missing/inapplicable as a
    # distinct response even when a training fold lacks that category.
    return Pipeline([
        ("indicators", OneHotEncoder(categories=[("y", "n", "-")] * len(PREDICTORS),
                                     handle_unknown="error", drop=None)),
        ("logistic", LogisticRegression(C=regularisation_c, solver="lbfgs", l1_ratio=0,
                                        class_weight=None, random_state=SEED,
                                        max_iter=MAX_ITERATIONS, tol=TOLERANCE)),
    ])


def evaluate_logistic(population: BenchmarkPopulation, plan: PartitionPlan) -> LogisticResult:
    """Tune C on development folds, refit on development, then score the test.

    Each fit uses a fresh encoding/classifier pipeline. Equal CV agreement
    favours the smallest C (strongest regularisation); test scores never enter
    selection. Only the fixed predictor allowlist reaches this boundary.

    Raises:
        ValidationError: Any candidate/refit fails or does not converge. The
            diagnostic omits library messages that could contain record values.
    """
    def evaluate(regularisation_c: float, training: tuple[int, ...],
                 evaluation: tuple[int, ...]) -> tuple[Scores, tuple[str, ...]]:
        model = _pipeline(regularisation_c)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                model.fit([population.features[i] for i in training],
                          [population.targets[i] for i in training])
            predicted = model.predict([population.features[i] for i in evaluation])
            actual = [population.targets[i] for i in evaluation]
            scores = Scores(float(accuracy_score(actual, predicted)),
                            float(f1_score(actual, predicted, average="macro",
                                           labels=list(population.retained_classes), zero_division=0)))
            return scores, tuple(predicted)
        except ConvergenceWarning:
            raise ValidationError(
                "logistic regression: fit did not converge; benchmark incomplete."
            ) from None
        except (ValueError, RuntimeError, FloatingPointError):
            raise ValidationError(
                "logistic regression: fitting or scoring failed; benchmark incomplete."
            ) from None

    candidates = tuple(
        CandidateResult(regularisation_c, tuple(evaluate(regularisation_c, fold.training, fold.validation)[0]
                                        for fold in plan.folds))
        for regularisation_c in C_VALUES
    )
    selected = min(candidates, key=lambda result: (-result.mean_cv_agreement, result.regularisation_c))
    test, predicted = evaluate(selected.regularisation_c, plan.development, plan.test)
    actual = [population.targets[i] for i in plan.test]
    per_cause = {}
    for label in sorted(population.retained_classes | population.excluded_classes):
        support = actual.count(label)
        recovered = sum(target == label and prediction == label
                        for target, prediction in zip(actual, predicted, strict=True))
        per_cause[label] = CauseRecall(support, recovered / support if support else None)
    return LogisticResult(candidates, selected, test, per_cause)
