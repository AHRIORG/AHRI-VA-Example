"""Fixed five-configuration selection with shared training-only preprocessing."""

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Literal
import warnings

from sklearn.ensemble import RandomForestClassifier
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


__all__ = ["CandidateResult", "CauseRecall", "LearnerResult", "Comparison", "evaluate_learners"]

C_VALUES = (0.1, 1.0, 10.0)
LEAF_SIZES = (1, 5)
TREE_COUNT = 200
MAX_ITERATIONS = 1000
TOLERANCE = 1e-4
LearnerName = Literal["Logistic regression", "Random forest"]


@dataclass(frozen=True)
class CandidateResult:
    """One learner setting (C or minimum leaf size) and its three fold scores."""

    setting: float | int
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
class LearnerResult:
    """Aggregate tuning and test results; no predictions or fitted models."""

    candidates: tuple[CandidateResult, ...]
    selected: CandidateResult
    test: Scores
    per_cause: dict[str, CauseRecall]
    confusions: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class Comparison:
    """Both fitted learners' aggregates and the development-selected name."""

    logistic: LearnerResult
    forest: LearnerResult
    selected: LearnerName

    @property
    def selected_result(self) -> LearnerResult:
        """Return aggregates for the learner fixed by development CV."""
        return self.logistic if self.selected == "Logistic regression" else self.forest


def _pipeline(learner: LearnerName, setting: float | int) -> Pipeline:
    # Categories come from the accepted contract, never from held-out records.
    # Every training pipeline retains missing/inapplicable as a distinct state.
    if learner == "Logistic regression":
        classifier = LogisticRegression(C=setting, solver="lbfgs", l1_ratio=0,
                                        class_weight=None, random_state=SEED,
                                        max_iter=MAX_ITERATIONS, tol=TOLERANCE)
    else:
        classifier = RandomForestClassifier(n_estimators=TREE_COUNT,
                                            min_samples_leaf=int(setting),
                                            class_weight=None, bootstrap=False,
                                            random_state=SEED, n_jobs=1)
    return Pipeline([
        ("indicators", OneHotEncoder(categories=[("y", "n", "-")] * len(PREDICTORS),
                                     handle_unknown="error", drop=None)),
        ("classifier", classifier),
    ])


def _evaluate(learner: LearnerName, setting: float | int, population: BenchmarkPopulation,
              training: tuple[int, ...], evaluation: tuple[int, ...]) -> tuple[Scores, tuple[str, ...]]:
    model = _pipeline(learner, setting)
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
            f"{learner.lower()}: fit did not converge; benchmark incomplete."
        ) from None
    except (ValueError, RuntimeError, FloatingPointError):
        raise ValidationError(
            f"{learner.lower()}: fitting or scoring failed; benchmark incomplete."
        ) from None


def evaluate_learners(population: BenchmarkPopulation, plan: PartitionPlan) -> Comparison:
    """Select settings and learner on shared folds, then evaluate both on test.

    Exact ties favour smaller C, larger leaves, and logistic regression between
    learners. Every fit uses a fresh pipeline and only allowlisted predictors.
    All returned values are aggregates; predictions and models stay in memory.

    Raises:
        ValidationError: Any candidate/refit fails or does not converge, without
            library messages that could contain record values.
    """
    def candidates(learner: LearnerName, settings: tuple[float | int, ...]) -> tuple[CandidateResult, ...]:
        return tuple(CandidateResult(setting, tuple(
            _evaluate(learner, setting, population, fold.training, fold.validation)[0]
            for fold in plan.folds
        )) for setting in settings)

    logistic_candidates = candidates("Logistic regression", C_VALUES)
    forest_candidates = candidates("Random forest", LEAF_SIZES)
    logistic = min(logistic_candidates, key=lambda result: (-result.mean_cv_agreement, result.setting))
    forest = max(forest_candidates, key=lambda result: (result.mean_cv_agreement, result.setting))
    selected: LearnerName = ("Random forest" if forest.mean_cv_agreement > logistic.mean_cv_agreement
                             else "Logistic regression")

    def finish(learner: LearnerName, settings: tuple[CandidateResult, ...], chosen: CandidateResult) -> LearnerResult:
        test, predicted = _evaluate(learner, chosen.setting, population, plan.development, plan.test)
        actual = [population.targets[i] for i in plan.test]
        per_cause = {}
        for label in sorted(population.retained_classes | population.excluded_classes):
            support = actual.count(label)
            recovered = sum(target == label and prediction == label
                            for target, prediction in zip(actual, predicted, strict=True))
            per_cause[label] = CauseRecall(support, recovered / support if support else None)
        confusion_counts = Counter((target, prediction)
                                   for target, prediction in zip(actual, predicted, strict=True)
                                   if target != prediction)
        # Keep only repeated directed errors, at most three, with exact-label
        # ordering for ties. These are aggregate counts, never row predictions.
        frequent = sorted(confusion_counts, key=lambda pair: (-confusion_counts[pair], pair))
        confusions = tuple((target, prediction, confusion_counts[target, prediction])
                           for target, prediction in frequent[:3]
                           if confusion_counts[target, prediction] >= 2)
        return LearnerResult(settings, chosen, test, per_cause, confusions)

    return Comparison(finish("Logistic regression", logistic_candidates, logistic),
                      finish("Random forest", forest_candidates, forest), selected)
