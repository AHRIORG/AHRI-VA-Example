"""One shared, in-memory partition plan for validation and every learner."""

from collections import Counter
from dataclasses import dataclass

from sklearn import model_selection

from ahri_va.config import ValidationError
from ahri_va.population import BenchmarkPopulation

SEED = 42
TEST_FRACTION = 0.2
FOLD_COUNT = 3


@dataclass(frozen=True)
class Fold:
    """Indices into the retained population, never into the original input."""

    training: tuple[int, ...]
    validation: tuple[int, ...]


@dataclass(frozen=True)
class PartitionPlan:
    """Materialized once; all fold indices address the same retained population."""

    development: tuple[int, ...]
    test: tuple[int, ...]
    folds: tuple[Fold, ...]

    def summary(self, population: BenchmarkPopulation) -> dict[str, object]:
        def counts(indices: tuple[int, ...]) -> dict[str, int]:
            return dict(sorted(Counter(population.targets[i] for i in indices).items()))

        return {
            "seed": SEED, "requested_test_fraction": TEST_FRACTION,
            "development_size": len(self.development), "test_size": len(self.test),
            "development_class_counts": counts(self.development),
            "test_class_counts": counts(self.test),
            "folds": [{"fold": number, "training_size": len(fold.training),
                       "validation_size": len(fold.validation),
                       "training_class_counts": counts(fold.training),
                       "validation_class_counts": counts(fold.validation)}
                      for number, fold in enumerate(self.folds, 1)],
        }


def make_partitions(population: BenchmarkPopulation) -> PartitionPlan:
    """Use seed 42 once for the 80/20 split and shuffled stratified folds."""
    try:
        development, test = model_selection.train_test_split(
            list(range(len(population.targets))), test_size=TEST_FRACTION,
            stratify=population.targets, random_state=SEED,
        )
    except ValueError:
        raise ValidationError("partitions: cannot generate the fixed stratified 80/20 split; "
                              "protocol unchanged; no seed retry.") from None
    development = tuple(int(i) for i in development)
    test = tuple(int(i) for i in test)
    _check_disjoint(development, test, set(range(len(population.targets))), "holdout")
    if len(test) < len(population.retained_classes):
        raise ValidationError("partitions: inadequate test capacity for all retained classes.")
    _check_coverage(population, development, 3, "development")
    _check_coverage(population, test, 1, "test")
    labels = [population.targets[i] for i in development]
    splitter = model_selection.StratifiedKFold(n_splits=FOLD_COUNT, shuffle=True, random_state=SEED)
    try:
        folds = tuple(Fold(tuple(development[int(i)] for i in training),
                           tuple(development[int(i)] for i in validation))
                      for training, validation in splitter.split(development, labels))
    except (ValueError, IndexError):
        raise ValidationError("partitions: cannot generate three development folds; "
                              "protocol unchanged; no seed retry.") from None
    if len(folds) != FOLD_COUNT:
        raise ValidationError("partitions: require exactly three development folds.")
    for number, fold in enumerate(folds, 1):
        _check_disjoint(fold.training, fold.validation, set(development), f"fold {number}")
        _check_coverage(population, fold.training, 1, f"fold {number} training")
        _check_coverage(population, fold.validation, 1, f"fold {number} validation")
    validations = Counter(i for fold in folds for i in fold.validation)
    if validations != Counter(development):
        raise ValidationError("partitions: each development record must be validated exactly once.")
    return PartitionPlan(development, test, folds)


def _check_disjoint(left: tuple[int, ...], right: tuple[int, ...],
                    expected: set[int], portion: str) -> None:
    if (len(set(left)) != len(left) or len(set(right)) != len(right)
            or set(left) & set(right) or set(left) | set(right) != expected):
        raise ValidationError(f"partitions: {portion} must be disjoint, exhaustive and duplicate-free.")


def _check_coverage(population: BenchmarkPopulation, indices: tuple[int, ...],
                    minimum: int, portion: str) -> None:
    counts = Counter(population.targets[i] for i in indices)
    insufficient = sum(counts[label] < minimum for label in population.retained_classes)
    if insufficient:
        raise ValidationError(
            f"partitions: inadequate {portion} coverage; insufficient_classes={insufficient}; "
            f"require at least {minimum} per retained class; protocol unchanged; no seed retry."
        )
