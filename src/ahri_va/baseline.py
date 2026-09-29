"""Training-only most-frequent-label evaluation; predictions stay in memory."""

from dataclasses import dataclass
from statistics import mean

from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score

from ahri_va.config import ValidationError
from ahri_va.partitions import PartitionPlan
from ahri_va.population import BenchmarkPopulation


@dataclass(frozen=True)
class Scores:
    agreement: float
    macro_f1: float


@dataclass(frozen=True)
class BaselineResult:
    folds: tuple[Scores, ...]
    test: Scores

    @property
    def mean_cv_agreement(self) -> float:
        return mean(score.agreement for score in self.folds)


def evaluate_baseline(population: BenchmarkPopulation, plan: PartitionPlan) -> BaselineResult:
    """Fit separately within each fold, then on development for holdout scoring."""
    def evaluate(training: tuple[int, ...], evaluation: tuple[int, ...]) -> Scores:
        model = DummyClassifier(strategy="most_frequent")
        model.fit([population.features[i] for i in training],
                  [population.targets[i] for i in training])
        predicted = model.predict([population.features[i] for i in evaluation])
        actual = [population.targets[i] for i in evaluation]
        return Scores(float(accuracy_score(actual, predicted)),
                      float(f1_score(actual, predicted, average="macro",
                                     labels=list(population.retained_classes), zero_division=0)))

    try:
        folds = tuple(evaluate(fold.training, fold.validation) for fold in plan.folds)
        test = evaluate(plan.development, plan.test)
    except (ValueError, RuntimeError, FloatingPointError):
        raise ValidationError("baseline: fitting or scoring failed; benchmark incomplete.") from None
    return BaselineResult(folds, test)
