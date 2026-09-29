"""Public commands exercised only with generated, invented teaching records."""

import contextlib
import csv
import io
import json
from html import unescape
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ahri_va.cli import main

PREDICTORS = json.loads((ROOT / "scripts/documented-schema.json").read_text())["predictors"]


def _predict_invented_a(model, features):
    return ["Invented A"] * features.shape[0]


def _encoded_row_numbers(features):
    return tuple(sum(1 << bit for bit, cell in enumerate(row[:16]) if cell == "y")
                 for row in features)


def _selection_section(report):
    selected = next(line for line in report.splitlines() if line.startswith("Training-selected learner:"))
    return selected + report.split("## Development selection", 1)[1].split("## Per-cause", 1)[0]


class BenchmarkCommand(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.config = self.work / "config.json"
        self.config.write_bytes((ROOT / "config/validation.example.json").read_bytes())

    def prepare(self, counts, extra=(), encode_rows=False):
        records = [(f"INVENTED-{group}-{i}", "18", label)
                   for group, (label, count) in enumerate(counts.items())
                   for i in range(count)] + list(extra)
        with (self.work / "deaths.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["IIntID", "Age_in_years", "cause1_InterVA"])
            writer.writerows(records)
        with (self.work / "indicators.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["IIntID", *PREDICTORS])
            for index, (identifier, _, _) in enumerate(records):
                cells = (["y" if index & (1 << bit) else "n" for bit in range(16)] + ["-"] * 337
                         if encode_rows else ["y", "n", *(["-"] * 351)])
                writer.writerow([identifier, *cells])

    def command(self, command="validate", expected=0, extra=()):
        argv = [command, "--deaths", str(self.work / "deaths.csv"),
                "--indicators", str(self.work / "indicators.csv"),
                "--config", str(self.config), *extra]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.chdir(self.work), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main(argv)
        self.assertEqual(status, expected, out.getvalue() + err.getvalue())
        self.assertNotIn(str(self.work), out.getvalue() + err.getvalue())
        self.assertNotIn("INVENTED-", out.getvalue() + err.getvalue())
        if expected:
            self.assertEqual(out.getvalue(), "")
            return json.loads(err.getvalue())
        self.assertEqual(err.getvalue(), "")
        return json.loads(out.getvalue()) if command == "validate" else out.getvalue()

    def test_cutoff_is_applied_after_eligibility_without_relabelling(self):
        self.prepare({" Invented A ": 5, "invented a": 5, "Undetermined": 4,
                      "Invented rare": 4}, extra=[("INVENTED-child", "17", "Invented rare")])
        result = self.command()
        self.assertEqual(result["eligible_labelled_adults"], 18)
        self.assertEqual(result["exclusions"]["under_18"], 1)
        population = result["population"]
        self.assertEqual(population["retained_classes"], {" Invented A ": 5, "invented a": 5})
        self.assertEqual(population["excluded_classes"], {"Invented rare": 4, "Undetermined": 4})
        self.assertEqual(population["excluded_records"], 8)
        self.assertEqual(population["retained_records"], 10)
        self.assertAlmostEqual(population["retained_fraction"], 10 / 18)
        self.assertEqual(result["models_fitted"], 0)

    def test_insufficient_retained_classes_fail_with_explainable_coverage(self):
        for counts, extra, fraction in [
            ({}, [("INVENTED-child", "17", "A")], None),
            ({"Invented A": 4, "Undetermined": 4}, [], 0),
            ({"Undetermined": 5, "Invented rare": 4}, [], 5 / 9),
        ]:
            with self.subTest(counts=counts):
                self.prepare(counts, extra)
                result = self.command(expected=2)
                self.assertIn("at least two retained classes", " ".join(result["errors"]))
                self.assertEqual(result["summary"]["population"]["retained_fraction"], fraction)
                self.assertEqual(result["summary"]["models_fitted"], 0)
                if counts.get("Undetermined") == 5:
                    self.assertEqual(result["summary"]["population"]["retained_classes"],
                                     {"Undetermined": 5})

    def test_partitions_have_class_coverage_and_fixed_seed_repeatability(self):
        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5})
        result = self.command()
        self.assertEqual(result, self.command())
        self.assertEqual(result["benchmark_feasibility"], "feasible")
        plan = result["partitions"]
        self.assertEqual(plan["seed"], 42)
        self.assertEqual(plan["development_size"], 12)
        self.assertEqual(plan["test_size"], 3)
        self.assertEqual(plan["test_class_counts"], {"Invented A": 1, "Invented B": 1, "Undetermined": 1})
        self.assertEqual(len(plan["folds"]), 3)
        for fold in plan["folds"]:
            self.assertEqual(fold["training_size"], 8)
            self.assertEqual(fold["validation_size"], 4)
            self.assertEqual(set(fold["training_class_counts"]), {"Invented A", "Invented B", "Undetermined"})
            self.assertEqual(set(fold["validation_class_counts"]), {"Invented A", "Invented B", "Undetermined"})

    def test_infeasible_holdout_is_rejected_without_retry_or_cutoff_change(self):
        # Fault injection at the external random partition boundary. With counts
        # >=5 the normal splitter has sufficient capacity; guards must still run.
        self.prepare({"Invented A": 5, "Invented B": 5})
        cases = [
            ((tuple(range(9)), (9,)), "test capacity"),
            (((2, 3, 4, 5, 6, 7, 8, 9), (0, 1)), "test coverage"),
            (((0, 1, 5, 6, 7, 8, 9), (2, 3, 4)), "development coverage"),
            (((0, 1, 2, 3, 4, 5, 6, 7), (0, 8)), "disjoint"),
        ]
        for split, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                with patch("sklearn.model_selection.train_test_split", return_value=split) as draw:
                    result = self.command(expected=2)
                self.assertIn(diagnostic, " ".join(result["errors"]))
                self.assertEqual(draw.call_count, 1)
                self.assertEqual(result["summary"]["population"]["minimum_class_count"], 5)

    def test_baseline_report_has_worked_metrics_and_only_aggregate_output(self):
        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 4})
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        report = self.command("benchmark")
        self.assertEqual(report, self.command("benchmark"))
        self.assertIn("# Adult InterVA5 replication benchmark", report)
        self.assertIn("Training-selected learner:", report)
        self.assertIn("eligible labelled adults in retained classes", report)
        self.assertIn("InterVA5 assignments", report)
        self.assertIn("| Most-frequent training label | 38.89% | 50.00% | 0.3333 |", report)
        self.assertIn("10 / 14 (71.43%)", report)
        self.assertIn("Undetermined", report)
        self.assertIn("| 4 |", report)
        self.assertIn("Seed: 42", report)
        for package in ("Python", "ahri-va", "scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl"):
            self.assertIn(package, report)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_logistic_selection_reports_all_candidates_and_prefers_stronger_regularisation(self):
        # Identical features make all settings tie. With three equally frequent
        # causes, each fold recovers one of four records; the test recovers one
        # of three. These are worked counts, not a high-score requirement.
        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5})
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        report = self.command("benchmark")
        self.assertEqual(report, self.command("benchmark"))
        self.assertIn("# Adult InterVA5 replication benchmark", report)
        self.assertIn("Training-selected learner:", report)
        self.assertIn("| Logistic regression | 25.00% | 33.33% | 0.1667 |", report)
        for strength in ("0.1", "1", "10"):
            self.assertIn(f"| {strength} | 25.00% |", report)
        self.assertIn("Selected logistic-regression C: 0.1", report)
        self.assertIn("no weighting or resampling", report)
        self.assertIn("353", report)
        self.assertIn("y", report)
        self.assertIn("n", report)
        self.assertIn("missing/inapplicable", report)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_complete_comparison_selects_logistic_and_larger_leaf_on_cv_ties(self):
        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5})
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        report = self.command("benchmark")
        self.assertIn("# Adult InterVA5 replication benchmark", report)
        self.assertNotIn("Intermediate", report)
        self.assertIn("| Random forest | 25.00% | 33.33% | 0.1667 |", report)
        self.assertIn("Selected random-forest minimum leaf size: 5", report)
        self.assertIn("Training-selected learner: **Logistic regression**", report)
        self.assertIn("| 1 | 25.00% |", report)
        self.assertIn("| 5 | 25.00% |", report)
        self.assertIn("200 trees", report)
        self.assertEqual(report, self.command("benchmark"))
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_logistic_failed_fits_and_non_convergence_never_emit_partial_reports(self):
        from sklearn.exceptions import ConvergenceWarning
        from sklearn.linear_model import LogisticRegression

        self.prepare({"Invented A": 5, "Invented B": 5})
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        real_fit = LogisticRegression.fit
        for fail_at in (1, 5, 10):  # First candidate, later candidate, final refit.
            for failure in (ValueError, RuntimeError, FloatingPointError, ConvergenceWarning):
                with self.subTest(fail_at=fail_at, failure=failure):
                    calls = []

                    def fail_fit(model, *args, **kwargs):
                        calls.append(model.C)
                        if len(calls) == fail_at:
                            if failure is ConvergenceWarning:
                                warnings.warn("INVENTED-private diagnostic", failure)
                            else:
                                raise failure("INVENTED-private diagnostic")
                        return real_fit(model, *args, **kwargs)

                    with patch.object(LogisticRegression, "fit", fail_fit):
                        result = self.command("benchmark", expected=2)
                    self.assertEqual(len(calls), fail_at)
                    self.assertIn("benchmark incomplete", " ".join(result["errors"]))
                    self.assertIn("logistic", " ".join(result["errors"]))
                    if failure is ConvergenceWarning:
                        self.assertIn("converge", " ".join(result["errors"]))
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_training_selected_forest_diagnostics_survive_better_logistic_test_scores(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression

        self.prepare({"Invented A": 20, "Invented B": 20, "Invented rare": 4}, encode_rows=True)
        calls = {"logistic": 0, "forest": 0}

        def predictions(model, features):
            learner = "logistic" if isinstance(model, LogisticRegression) else "forest"
            calls[learner] += 1
            rows = features.toarray()
            numbers = [sum(1 << bit for bit in range(16) if row[3 * bit]) for row in rows]
            actual = ["Invented A" if number < 20 else "Invented B" for number in numbers]
            # Logistic: every CV prediction wrong, perfect test. Forest: leaf 1
            # perfect in CV, leaf 5 wrong; final test entirely wrong. The forest
            # must remain selected and supply all per-cause/confusion results.
            correct = (calls[learner] == 10 if learner == "logistic"
                       else calls[learner] < 7 and model.min_samples_leaf == 1)
            return actual if correct else ["Invented B" if label == "Invented A" else "Invented A"
                                           for label in actual]

        with patch.object(LogisticRegression, "predict", predictions), patch.object(
            RandomForestClassifier, "predict", predictions
        ):
            report = unescape(self.command("benchmark"))
        self.assertEqual(calls, {"logistic": 10, "forest": 7})
        self.assertIn("Training-selected learner: **Random forest**", report)
        self.assertIn("Selected random-forest minimum leaf size: 1", report)
        self.assertIn("| Logistic regression | 0.00% | 100.00% | 1.0000 |", report)
        self.assertIn("| Random forest | 100.00% | 0.00% | 0.0000 |", report)
        self.assertIn('| <code>"Invented A"</code> | 4 | 0.00% |', report)
        self.assertIn('| <code>"Invented B"</code> | 4 | 0.00% |', report)
        self.assertIn('| <code>"Invented rare"</code> | 0 | not estimable (excluded) |', report)
        self.assertIn('Recorded <code>"Invented A"</code> → predicted <code>"Invented B"</code>: 4 test records.', report)
        self.assertIn('Recorded <code>"Invented B"</code> → predicted <code>"Invented A"</code>: 4 test records.', report)

    def test_forest_failures_never_emit_partial_reports_or_artifacts(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.exceptions import ConvergenceWarning

        self.prepare({"Invented A": 5, "Invented B": 5})
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        real_fit = RandomForestClassifier.fit
        for fail_at in (1, 4, 7):  # First/later candidate and full-development refit.
            for failure in (ValueError, RuntimeError, FloatingPointError, ConvergenceWarning):
                with self.subTest(fail_at=fail_at, failure=failure):
                    calls = []

                    def fail_fit(model, *args, **kwargs):
                        calls.append(model.min_samples_leaf)
                        if len(calls) == fail_at:
                            if failure is ConvergenceWarning:
                                warnings.warn("INVENTED-private diagnostic", failure)
                            else:
                                raise failure("INVENTED-private diagnostic")
                        return real_fit(model, *args, **kwargs)

                    with patch.object(RandomForestClassifier, "fit", fail_fit):
                        result = self.command("benchmark", expected=2)
                    self.assertEqual(len(calls), fail_at)
                    self.assertIn("random forest", " ".join(result["errors"]))
                    self.assertIn("benchmark incomplete", " ".join(result["errors"]))
        with patch.object(RandomForestClassifier, "predict", side_effect=ValueError("INVENTED-private")):
            self.command("benchmark", expected=2)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_logistic_report_distinguishes_zero_recall_from_absent_support(self):
        from sklearn.linear_model import LogisticRegression

        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5,
                      "Invented rare": 4})
        # A controlled estimator boundary gives a worked confusion pattern:
        # one of three test labels recovered, F1(A)=1/2, macro F1=1/6.
        with patch.object(LogisticRegression, "predict", _predict_invented_a):
            report = unescape(self.command("benchmark"))
        self.assertIn("| Logistic regression | 33.33% | 33.33% | 0.1667 |", report)
        self.assertIn("Test support | Selected-learner recall", report)
        self.assertIn('| <code>"Invented A"</code> | 1 | 100.00% |', report)
        self.assertIn('| <code>"Invented B"</code> | 1 | 0.00% |', report)
        self.assertIn('| <code>"Undetermined"</code> | 1 | 0.00% |', report)
        self.assertIn('| <code>"Invented rare"</code> | 0 | not estimable (excluded) |', report)
        self.assertIn("eligible labelled adults in retained classes", report)

    def test_five_configuration_budget_encoding_and_shared_partitions_are_training_only(self):
        from sklearn import model_selection
        from sklearn.dummy import DummyClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder

        self.prepare({"Invented A": 5, "Invented B": 6, "Undetermined": 7,
                      "Invented rare": 4}, encode_rows=True)
        splits, folds, baseline_fits, pipeline_fits, encoder_fits = [], [], [], [], []
        baseline_tests, pipeline_tests, settings = [], [], []
        forest_settings = []
        real_split = model_selection.train_test_split
        real_folds = model_selection.StratifiedKFold.split
        real_baseline_fit, real_baseline_predict = DummyClassifier.fit, DummyClassifier.predict
        real_pipeline_fit, real_pipeline_predict = Pipeline.fit, Pipeline.predict
        real_encoder_fit, real_logistic_fit = OneHotEncoder.fit, LogisticRegression.fit
        real_forest_fit = RandomForestClassifier.fit

        def observe_split(*args, **kwargs):
            result = real_split(*args, **kwargs)
            splits.append(result)
            self.assertEqual(kwargs["random_state"], 42)
            return result

        def observe_folds(splitter, *args, **kwargs):
            result = list(real_folds(splitter, *args, **kwargs))
            folds.append(result)
            return iter(result)

        def observe_baseline_fit(model, features, labels, **kwargs):
            baseline_fits.append(_encoded_row_numbers(features))
            return real_baseline_fit(model, features, labels, **kwargs)

        def observe_baseline_predict(model, features):
            baseline_tests.append(_encoded_row_numbers(features))
            return real_baseline_predict(model, features)

        def observe_pipeline_fit(model, features, labels, **kwargs):
            pipeline_fits.append(_encoded_row_numbers(features))
            self.assertTrue(all(len(row) == 353 for row in features))
            return real_pipeline_fit(model, features, labels, **kwargs)

        def observe_pipeline_predict(model, features, **kwargs):
            pipeline_tests.append(_encoded_row_numbers(features))
            return real_pipeline_predict(model, features, **kwargs)

        def observe_encoder_fit(encoder, features, labels=None):
            encoder_fits.append(_encoded_row_numbers(features))
            result = real_encoder_fit(encoder, features, labels)
            self.assertEqual([tuple(states) for states in encoder.categories_],
                             [("y", "n", "-")] * 353)
            # Every category must activate its own column, including a category
            # absent from training. Probe only this disposable fixture encoder.
            probes = [[state] + ["n"] * 352 for state in ("y", "n", "-")]
            encoded = encoder.transform(probes).toarray()
            self.assertEqual(encoded.shape, (3, 1059))
            self.assertEqual(encoded[:, :3].tolist(), [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            return result

        def observe_logistic_fit(model, features, labels, sample_weight=None, **kwargs):
            settings.append(model.C)
            self.assertIsNone(model.class_weight)
            self.assertIsNone(sample_weight)
            self.assertEqual(model.random_state, 42)
            self.assertEqual(model.solver, "lbfgs")
            self.assertEqual(model.l1_ratio, 0)
            return real_logistic_fit(model, features, labels, sample_weight=sample_weight, **kwargs)

        def observe_forest_fit(model, features, labels, sample_weight=None, **kwargs):
            forest_settings.append(model.min_samples_leaf)
            self.assertEqual(model.n_estimators, 200)
            self.assertEqual(model.random_state, 42)
            self.assertIsNone(model.class_weight)
            self.assertIsNone(sample_weight)
            self.assertFalse(model.bootstrap)
            return real_forest_fit(model, features, labels, sample_weight=sample_weight, **kwargs)

        with patch.object(LogisticRegression, "fit", side_effect=AssertionError("validate fitted")), patch.object(
            OneHotEncoder, "fit", side_effect=AssertionError("validate fitted preprocessing")
        ), patch.object(
            RandomForestClassifier, "fit", side_effect=AssertionError("validate fitted a forest")
        ):
            self.assertEqual(self.command()["models_fitted"], 0)
        with patch.object(model_selection, "train_test_split", observe_split), patch.object(
            model_selection.StratifiedKFold, "split", observe_folds
        ), patch.object(DummyClassifier, "fit", observe_baseline_fit), patch.object(
            DummyClassifier, "predict", observe_baseline_predict
        ), patch.object(Pipeline, "fit", observe_pipeline_fit), patch.object(
            Pipeline, "predict", observe_pipeline_predict
        ), patch.object(OneHotEncoder, "fit", observe_encoder_fit), patch.object(
            LogisticRegression, "fit", observe_logistic_fit
        ), patch.object(
            RandomForestClassifier, "fit", observe_forest_fit
        ):
            report = self.command("benchmark")
        self.assertEqual(len(splits), 1)
        self.assertEqual(len(folds), 1)
        self.assertEqual(len(pipeline_fits), 17)  # Five settings x three folds, two refits.
        self.assertEqual(settings[:9], [0.1] * 3 + [1] * 3 + [10] * 3)
        self.assertEqual(len(settings), 10)
        self.assertEqual(forest_settings[:6], [1] * 3 + [5] * 3)
        self.assertEqual(len(forest_settings), 7)
        self.assertIn(f"Selected logistic-regression C: {settings[-1]:g}", report)
        self.assertIn(f"Selected random-forest minimum leaf size: {forest_settings[-1]}", report)
        self.assertEqual(encoder_fits, pipeline_fits)
        for offset in (0, 3, 6, 9, 12):
            self.assertEqual(pipeline_fits[offset:offset + 3], baseline_fits[:3])
            self.assertEqual(pipeline_tests[offset:offset + 3], baseline_tests[:3])
        for offset in (-2, -1):
            self.assertEqual(pipeline_fits[offset], baseline_fits[-1])
            self.assertEqual(pipeline_tests[offset], baseline_tests[-1])
        development, test = splits[0]
        self.assertEqual(pipeline_fits[-1], tuple(development))
        self.assertEqual(pipeline_tests[-1], tuple(test))
        for seen in pipeline_fits:
            self.assertEqual(len(seen), len(set(seen)))  # No oversampling.
            self.assertFalse(set(seen) & set(test))
            self.assertTrue(set(seen) <= set(range(18)))  # Rare class never fitted.
        for seen, (training, validation) in zip(pipeline_fits[:3], folds[0], strict=True):
            self.assertEqual(seen, tuple(development[int(i)] for i in training))
            self.assertFalse(set(seen) & {development[int(i)] for i in validation})

    def test_selection_uses_mean_fold_agreement_and_breaks_a_nondefault_tie(self):
        from sklearn.linear_model import LogisticRegression

        self.prepare({"Invented A": 5, "Invented B": 5}, encode_rows=True)
        prediction_calls = []

        def controlled_predictions(model, features):
            # In this fixture, the first 16 indicators encode the row number.
            encoded = features.toarray()
            rows = [sum(1 << bit for bit in range(16) if row[3 * bit]) for row in encoded]
            actual = ["Invented A" if number < 5 else "Invented B" for number in rows]
            prediction_calls.append(model.C)
            if len(prediction_calls) == 10:
                correct = 0  # A poor holdout result must not trigger reselection.
            elif model.C == 0.1:
                correct = 1 if len(rows) == 3 else 0
            else:
                correct = 2 if len(rows) == 2 else 0
            return [label if i < correct else ("Invented B" if label == "Invented A" else "Invented A")
                    for i, label in enumerate(actual)]

        with patch.object(LogisticRegression, "predict", controlled_predictions):
            report = self.command("benchmark")
        # Both settings get 2/8 pooled predictions right. Unweighted fold means
        # are 22.22% versus 33.33%, so C=1 wins, tied with C=10.
        self.assertIn("| 0.1 | 22.22% |", report)
        self.assertIn("| 1 | 33.33% |", report)
        self.assertIn("| 10 | 33.33% |", report)
        self.assertIn("Selected logistic-regression C: 1;", report)
        self.assertEqual(prediction_calls, [0.1] * 3 + [1] * 3 + [10] * 3 + [1])
        self.assertIn("| Logistic regression | 33.33% | 0.00% | 0.0000 |", report)

    def test_holdout_perturbations_cannot_change_fits_or_selection(self):
        from sklearn import model_selection
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression

        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5}, encode_rows=True)
        real_split, real_fit = model_selection.train_test_split, LogisticRegression.fit
        real_forest_fit = RandomForestClassifier.fit
        holdout, fitted = [], []

        def observe_split(*args, **kwargs):
            development, test = real_split(*args, **kwargs)
            holdout[:] = test
            return development, test

        def observe_fit(model, features, labels, **kwargs):
            result = real_fit(model, features, labels, **kwargs)
            fitted.append((model.C, features.toarray().tolist(), list(labels),
                           model.coef_.tolist(), model.intercept_.tolist()))
            return result

        def observe_forest_fit(model, features, labels, **kwargs):
            result = real_forest_fit(model, features, labels, **kwargs)
            fitted.append((model.min_samples_leaf, features.toarray().tolist(), list(labels),
                           [tree.tree_.threshold.tolist() for tree in model.estimators_],
                           [tree.tree_.value.tolist() for tree in model.estimators_]))
            return result

        with patch.object(model_selection, "train_test_split", observe_split), patch.object(
            LogisticRegression, "fit", observe_fit
        ), patch.object(
            RandomForestClassifier, "fit", observe_forest_fit
        ):
            original = self.command("benchmark")
        original_fits = fitted.copy()
        with (self.work / "indicators.csv").open(newline="") as stream:
            rows = list(csv.reader(stream))
        for index in holdout:
            # All three allowed categories change; neither IDs nor targets do.
            rows[index + 1][1:] = [{"y": "n", "n": "-", "-": "y"}[cell]
                                   for cell in rows[index + 1][1:]]
        with (self.work / "indicators.csv").open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)
        fitted.clear()
        with patch.object(LogisticRegression, "fit", observe_fit), patch.object(
            RandomForestClassifier, "fit", observe_forest_fit
        ):
            perturbed = self.command("benchmark")
        self.assertEqual(fitted, original_fits)
        # Compare the entire development selection table, never holdout scores.
        self.assertEqual(_selection_section(original), _selection_section(perturbed))

    def test_excluded_fields_and_reviewed_blank_mapping_preserve_benchmark_results(self):
        self.prepare({"Invented A": 5, "Invented B": 5, "Undetermined": 5}, encode_rows=True)
        original = self.command("benchmark")
        for role in ("deaths", "indicators"):
            path = self.work / (role + ".csv")
            with path.open(newline="") as stream:
                rows = list(csv.reader(stream))
            extra_fields = ["Questionnaire", "covid_test_r", "cause2_InterVA", "i_not_allowlisted"]
            if role == "indicators":
                extra_fields += ["cause1_InterVA", "Age_in_years"]
            rows[0].extend(extra_fields)
            for index, row in enumerate(rows[1:]):
                row[0] = f"INVENTED-REKEYED-{index}"  # Same lossless linkage in both files.
                if role == "deaths":
                    row[1] = "99"  # Remains eligible, cannot become a predictor.
                row.extend([f"INVENTED-EXCLUDED-{index}"] * len(extra_fields))
            with path.open("w", newline="") as stream:
                csv.writer(stream).writerows(rows)
        self.assertEqual(original, self.command("benchmark"))
        path = self.work / "indicators.csv"
        with path.open(newline="") as stream:
            rows = list(csv.reader(stream))
        rows[1][353] = ""  # Originally missing/inapplicable, within the allowlist.
        with path.open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)
        self.assertIn("undeclared_values", " ".join(self.command("benchmark", expected=2)["errors"]))
        config = json.loads(self.config.read_text())
        config["indicator_blank_mapping"] = "missing_inapplicable"
        config["indicator_blank_mapping_reviewed"] = True
        self.config.write_text(json.dumps(config))
        self.assertEqual(original, self.command("benchmark"))
        rows[1][353] = "INVENTED-INVALID-STATE"
        with path.open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)
        self.assertIn("undeclared_values", " ".join(self.command("benchmark", expected=2)["errors"]))

    def test_exact_labels_are_safely_rendered_without_changing_the_experiment(self):
        self.prepare({' <b>Invented | cause</b> ': 5, 'Invented `cause` & B': 5,
                      'Rare | <script>invented</script>': 4})
        report = self.command("benchmark")
        self.assertNotIn("<script>", report)
        self.assertNotIn("<b>", report)
        self.assertIn("&#124;", report)
        self.assertIn('" <b>Invented | cause</b> "', unescape(report))
        self.assertIn("| Most-frequent training label | 38.89% | 50.00% | 0.3333 |", report)

    def test_markdown_in_labels_cannot_create_links_images_or_formatting(self):
        label = '![Invented image](https://example.invalid/x) `code` **bold**'
        self.prepare({label: 5, 'Invented B': 5})
        report = self.command("benchmark")
        self.assertNotIn('![Invented image]', report)
        self.assertNotIn('`code`', report)
        self.assertNotIn('**bold**', report)
        self.assertIn(json.dumps(label), unescape(report))

    def test_missing_fold_coverage_and_splitter_failure_stop_the_command(self):
        self.prepare({"Invented A": 5, "Invented B": 5})
        for fold, diagnostic in [
            (((4, 5, 6, 7), (0, 1, 2, 3)), "fold 1 training coverage"),
            (((1, 2, 3, 4, 5, 6, 7), (0,)), "fold 1 validation coverage"),
        ]:
            with self.subTest(diagnostic=diagnostic):
                with patch("sklearn.model_selection.train_test_split",
                           return_value=((0, 1, 2, 3, 5, 6, 7, 8), (4, 9))), patch(
                    "sklearn.model_selection.StratifiedKFold.split", return_value=iter([fold] * 3)
                ) as draw:
                    result = self.command(expected=2)
                self.assertIn(diagnostic, " ".join(result["errors"]))
                self.assertEqual(draw.call_count, 1)

    def test_baseline_uses_shared_training_partitions_and_validate_never_fits(self):
        # Observe external sklearn APIs, without replacing application helpers.
        from sklearn.dummy import DummyClassifier
        from sklearn import model_selection

        self.prepare({"Invented A": 5, "Invented B": 6, "Invented rare": 4}, encode_rows=True)
        fitted_rows, splits, folds = [], [], []
        real_fit = DummyClassifier.fit
        real_split = model_selection.train_test_split
        real_folds = model_selection.StratifiedKFold.split

        def observe_fit(model, features, labels, **kwargs):
            fitted_rows.append({sum(1 << bit for bit, cell in enumerate(row[:16]) if cell == "y")
                                for row in features})
            return real_fit(model, features, labels, **kwargs)

        def observe_split(*args, **kwargs):
            result = real_split(*args, **kwargs)
            splits.append(result)
            return result

        def observe_folds(splitter, *args, **kwargs):
            result = list(real_folds(splitter, *args, **kwargs))
            folds.append(result)
            return iter(result)

        with patch.object(DummyClassifier, "fit", side_effect=AssertionError("validate fitted a model")):
            validation = self.command()
        self.assertEqual(validation["models_fitted"], 0)
        with patch.object(DummyClassifier, "fit", observe_fit), patch.object(
            model_selection, "train_test_split", observe_split
        ), patch.object(model_selection.StratifiedKFold, "split", observe_folds):
            self.command()
            report = self.command("benchmark")
        self.assertEqual(len(splits), 2)  # Once for each command, never for each learner/fold.
        self.assertEqual(splits[0], splits[1])
        self.assertEqual(len(folds), 2)
        self.assertEqual([[ (a.tolist(), b.tolist()) for a, b in run] for run in folds][0],
                         [[ (a.tolist(), b.tolist()) for a, b in run] for run in folds][1])
        development, test = splits[1]
        self.assertEqual(set(development) | set(test), set(range(11)))
        self.assertEqual(len(fitted_rows), 4)
        self.assertEqual(fitted_rows[-1], set(development))
        for seen, (training, validation) in zip(fitted_rows[:3], folds[1], strict=True):
            self.assertEqual(seen, {development[int(i)] for i in training})
            self.assertFalse(seen & {development[int(i)] for i in validation})
        for seen in fitted_rows:
            self.assertFalse(seen & set(test))
        # Full population majority is B, but development ties choose A. A fit
        # using holdout labels would incorrectly score 66.67% rather than 33.33%.
        self.assertIn("| Most-frequent training label | 38.89% | 33.33% | 0.2500 |", report)

    def test_benchmark_shares_input_failures_and_produces_no_partial_report(self):
        self.prepare({"Invented A": 5, "Invented B": 5})
        with (self.work / "deaths.csv").open("a") as stream:
            stream.write("INVENTED-0-0,18,Invented A\n")
        self.assertEqual(self.command(expected=2), self.command("benchmark", expected=2))
        self.prepare({"Invented A": 4})
        self.assertEqual(self.command(expected=2), self.command("benchmark", expected=2))
        self.prepare({"Invented A": 5, "Invented B": 5})
        with patch("sklearn.dummy.DummyClassifier.fit", side_effect=ValueError("INVENTED-private")):
            failed = self.command("benchmark", expected=2)
        self.assertIn("benchmark incomplete", " ".join(failed["errors"]))
        for boundary in ("train_test_split", "StratifiedKFold.split"):
            with self.subTest(boundary=boundary), patch(
                "sklearn.model_selection." + boundary, side_effect=ValueError("INVENTED-private")
            ) as draw:
                result = self.command(expected=2)
                self.assertIn("partitions", " ".join(result["errors"]))
                self.assertEqual(draw.call_count, 1)


if __name__ == "__main__":
    unittest.main()
