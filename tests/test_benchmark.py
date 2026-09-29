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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ahri_va.cli import main

PREDICTORS = json.loads((ROOT / "scripts/documented-schema.json").read_text())["predictors"]


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
        self.assertIn("Baseline milestone", report)
        self.assertIn("Ticket 05", report)
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
