"""Aggregate-only Markdown for the intermediate two-model comparison."""

from importlib.metadata import PackageNotFoundError, version
import json
import platform
import string

from ahri_va.baseline import BaselineResult
from ahri_va.logistic import LogisticResult, MAX_ITERATIONS, TOLERANCE
from ahri_va.partitions import PartitionPlan, SEED
from ahri_va.population import BenchmarkPopulation
from ahri_va.validation import EligibleInputs


__all__ = ["comparison_report"]


def _label(label: str) -> str:
    # Inline HTML alone does not suppress Markdown. Encode punctuation one
    # character at a time, so neither HTML nor Markdown can interpret the label.
    quoted = json.dumps(label, ensure_ascii=False)
    literal = "".join(f"&#{ord(character)};" if character in string.punctuation else character
                      for character in quoted)
    return f"<code>{literal}</code>"


def comparison_report(eligible: EligibleInputs, population: BenchmarkPopulation,
                      plan: PartitionPlan, result: BaselineResult, logistic: LogisticResult) -> str:
    """Render counts and scores only; never include paths, row IDs or predictions."""
    retained = len(population.targets)
    lines = [
        "# Intermediate comparison — adult InterVA5 replication", "",
        "Agreement measures replication of InterVA5 assignments among eligible labelled adults in retained classes.",
        "It does not establish accuracy against independently determined causes of death or performance across all adult causes.",
        "This is the Ticket 04 two-model milestone; random forests and final learner selection belong to Ticket 05.", "",
        "## Held-out agreement", "",
        "| Model | Mean development CV agreement | Test exact-match agreement | Test macro F1 |",
        "| --- | ---: | ---: | ---: |",
        f"| Most-frequent training label | {result.mean_cv_agreement:.2%} | {result.test.agreement:.2%} | {result.test.macro_f1:.4f} |",
        f"| Logistic regression | {logistic.selected.mean_cv_agreement:.2%} | {logistic.test.agreement:.2%} | {logistic.test.macro_f1:.4f} |", "",
        "Each fold uses only its training labels. The final baseline uses the full development portion.",
        "Equal training counts select the lexicographically first exact label. The holdout is used only for final evaluation.",
        "Macro F1 weights retained classes equally; a supported class with no correct predictions contributes zero.", "",
        "## Logistic-regression selection", "",
        f"Selected logistic-regression C: {logistic.selected.regularisation_c:g}; chosen using mean development CV exact-match agreement only.",
        "Equal scores favour the smaller C (stronger regularisation). Both models use the same development folds and final test records.",
        "Test results cannot change the selected setting or protocol; no final learner has been selected in this intermediate comparison.", "",
        "| C | Mean development CV agreement |", "| ---: | ---: |",
    ]
    lines += [f"| {candidate.regularisation_c:g} | {candidate.mean_cv_agreement:.2%} |"
              for candidate in logistic.candidates]
    lines += ["", "## Per-cause test recovery", "",
              "Recall is the fraction of a cause's test records recovered by logistic regression.",
              "Excluded classes are not evaluated; no test support means not estimable, not zero recall.",
              "Every retained class has test support; small counts do not establish reliable cause-specific performance.", "",
              "| Class | Test support | Logistic-regression recall |", "| --- | ---: | ---: |"]
    for label, recovery in logistic.per_cause.items():
        recall = f"{recovery.recall:.2%}" if recovery.recall is not None else "not estimable"
        if label in population.excluded_classes:
            recall += " (excluded)"
        lines.append(f"| {_label(label)} | {recovery.support} | {recall} |")
    lines += ["",
        "## Inclusion and exclusion", "",
        "| Input | Rows | Missing identifiers | Unmatched | Matched |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for role, counts in eligible.summary["inputs"].items():
        lines.append(f"| {role} | {counts['rows']} | {counts['missing_identifiers']} | {counts['unmatched']} | {eligible.summary['matched_records']} |")
    lines += ["", "Among matched records, exclusions apply sequentially in this order:", "",
              "| Stage | Excluded | Remaining |", "| --- | ---: | ---: |"]
    remaining = eligible.summary["matched_records"]
    for reason, count in eligible.summary["exclusions"].items():
        remaining -= count
        lines.append(f"| {reason.replace('_', ' ')} | {count} | {remaining} |")
    lines += [f"| Classes with fewer than five eligible adults | {sum(population.excluded_classes.values())} | {retained} |", "",
              f"Retained coverage: {retained} / {population.eligible_count} ({retained / population.eligible_count:.2%}) otherwise eligible labelled adults.",
              "An empty denominator is not estimable and cannot produce a successful benchmark.", "",
              "### Excluded exact classes", ""]
    if population.excluded_classes:
        lines += ["| Excluded class | Eligible count |", "| --- | ---: |"]
        lines += [f"| {_label(label)} | {count} |" for label, count in population.excluded_classes.items()]
    else:
        lines.append("None.")
    lines += ["", "### Retained exact classes", "",
              "| Class | Eligible count | Development | Test |", "| --- | ---: | ---: | ---: |"]
    for label, count in population.retained_classes.items():
        development = sum(population.targets[i] == label for i in plan.development)
        test = sum(population.targets[i] == label for i in plan.test)
        lines.append(f"| {_label(label)} | {count} | {development} | {test} |")
    lines += ["", "## Reproducibility", "", f"Seed: {SEED}. Fixed cutoff: five eligible labelled adults per exact class.",
              f"Stratified development/test split: {len(plan.development)} / {len(plan.test)} records (requested 80/20).",
              "Three stratified development folds, shuffled with seed 42; all class-coverage checks passed.",
              "Same input order and package versions are required to reproduce record membership.", "",
              "| Fold | Training | Validation | Baseline agreement | Logistic agreement |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for number, (fold, scores, logistic_scores) in enumerate(
        zip(plan.folds, result.folds, logistic.selected.folds, strict=True), 1
    ):
        lines.append(f"| {number} | {len(fold.training)} | {len(fold.validation)} | {scores.agreement:.2%} | {logistic_scores.agreement:.2%} |")
    lines += ["", "Baseline setting: `DummyClassifier(strategy=\"most_frequent\")`; no tuning, weighting or resampling.",
              "Logistic regression: L2 regularisation, lbfgs solver, multinomial loss for three or more classes (binary logistic loss for two).",
              f"Maximum iterations: {MAX_ITERATIONS}; tolerance: {TOLERANCE:g}; random_state: {SEED}; no weighting or resampling.",
              "Encoding: all 353 allowlisted indicators; explicit y, n and - (missing/inapplicable) one-hot categories, with none dropped.",
              "Each fold fits a fresh encoding/classifier pipeline on its training portion only; the chosen pipeline is refit on full development.",
              "", "| Package | Version |", "| --- | --- |", f"| Python | {platform.python_version()} |"]
    for package in ("ahri-va", "scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl"):
        try:
            installed = version(package)
        except PackageNotFoundError:
            installed = "uninstalled source"
        lines.append(f"| {package} | {installed} |")
    lines += ["", "Predictions and fitted models remain in memory; no individual-prediction or fitted-model files are produced.",
              "Real-data reports remain in the analysis account until the user releases reviewed aggregates.", ""]
    return "\n".join(lines)
