"""Exact-class exclusion after input, linkage and adult/target eligibility."""

from collections import Counter
from dataclasses import dataclass

from ahri_va.validation import EligibleInputs

MIN_CLASS_COUNT = 5


@dataclass(frozen=True)
class BenchmarkPopulation:
    """Retained rows in input order, with exact class labels and coverage counts."""

    features: tuple[tuple[str, ...], ...]
    targets: tuple[str, ...]
    retained_classes: dict[str, int]
    excluded_classes: dict[str, int]
    eligible_count: int

    def summary(self) -> dict[str, object]:
        return {
            "minimum_class_count": MIN_CLASS_COUNT,
            "retained_classes": self.retained_classes,
            "excluded_classes": self.excluded_classes,
            "excluded_records": sum(self.excluded_classes.values()),
            "retained_records": len(self.targets),
            "retained_fraction": len(self.targets) / self.eligible_count
            if self.eligible_count else None,
        }


def retain_classes(eligible: EligibleInputs) -> BenchmarkPopulation:
    counts = Counter(eligible.targets)
    retained = {label: counts[label] for label in sorted(counts) if counts[label] >= MIN_CLASS_COUNT}
    excluded = {label: counts[label] for label in sorted(counts) if counts[label] < MIN_CLASS_COUNT}
    indices = [i for i, label in enumerate(eligible.targets) if label in retained]
    return BenchmarkPopulation(
        tuple(eligible.features[i] for i in indices), tuple(eligible.targets[i] for i in indices),
        retained, excluded, len(eligible.targets),
    )
