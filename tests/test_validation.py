"""Exercise the public command using temporary, explicitly invented records."""

import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ahri_va.cli import main


SCHEMA = json.loads((ROOT / "scripts/documented-schema.json").read_text(encoding="utf-8"))
PREDICTORS = SCHEMA["predictors"]


class ValidateCommand(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.config = json.loads((ROOT / "config/validation.example.json").read_text())
        self.save_config()
        self.prepare()

    def save_config(self):
        (self.work / "config.json").write_text(json.dumps(self.config), encoding="utf-8")

    def table(self, role, records, fields=None):
        if fields is None:
            fields = (["IIntID", "Age_in_years", "cause1_InterVA"] if role == "deaths"
                      else ["IIntID", *PREDICTORS])
        path = self.work / (role + ".csv")
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for record in records:
                row = dict.fromkeys(fields, "-" if role == "indicators" else "")
                row.update(record)
                writer.writerow(row)
        return path

    def prepare(self, deaths=None, indicators=None):
        if deaths is None:
            deaths = [{"IIntID": "INVENTED-001", "Age_in_years": "18",
                       "cause1_InterVA": "Invented cause A"}]
        if indicators is None:
            indicators = [{"IIntID": row["IIntID"]} for row in deaths]
        self.table("deaths", deaths)
        self.table("indicators", indicators)

    def run_command(self, expected=None, argv=None):
        # These Ticket 02 fixtures deliberately contain too few eligible adults
        # for Ticket 03. Still assert their input/eligibility counts through the
        # public command's explicit population-failure summary.
        population_failure = expected is None
        if population_failure:
            expected = 2
        if argv is None:
            argv = ["validate", "--deaths", str(self.work / "deaths.csv"),
                    "--indicators", str(self.work / "indicators.csv"),
                    "--config", str(self.work / "config.json")]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main(argv)
        self.assertEqual(status, expected, out.getvalue() + err.getvalue())
        self.assertNotIn(self.temp.name, out.getvalue() + err.getvalue())
        self.assertNotIn("SENSITIVE-INVENTED", out.getvalue() + err.getvalue())
        if expected:
            self.assertEqual(out.getvalue(), "")
            failure = json.loads(err.getvalue())
            if population_failure:
                self.assertIn("population: require at least two retained classes", " ".join(failure["errors"]))
                return failure["summary"]
            return failure
        self.assertEqual(err.getvalue(), "")
        return json.loads(out.getvalue())

    def test_eligible_input_can_fail_population_checks_without_creating_artifacts(self):
        before = {path.name: path.read_bytes() for path in self.work.iterdir()}
        result = self.run_command()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["eligible_labelled_adults"], 1)
        self.assertEqual(result["predictor_count"], 353)
        self.assertEqual(result["models_fitted"], 0)
        self.assertEqual(result["benchmark_feasibility"], "infeasible")
        self.assertEqual(result["eligible_indicator_states"], {"y": 0, "n": 0, "-": 353})
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.work.iterdir()})

    def test_age_boundary_and_exclusions_are_sequential_and_reconcile(self):
        ages = ["18", "17", "18.0", "1.8e1", "0", "", "-1", "18.5", "NaN", "Infinity",
                " 18", "18 ", "1_8", "SENSITIVE-INVENTED-AGE", "20", "21", "22", "23"]
        records = [{"IIntID": f"INVENTED-{i}", "Age_in_years": age,
                    "cause1_InterVA": "Invented A"} for i, age in enumerate(ages)]
        records[5]["cause1_InterVA"] = ""  # Count only the earlier age exclusion.
        records[14]["cause1_InterVA"] = ""
        records[15]["cause1_InterVA"] = " \t "
        records[16]["cause1_InterVA"] = "SENSITIVE-INVENTED\x00TARGET"
        records[17]["cause1_InterVA"] = "Undetermined"
        self.prepare(records)
        result = self.run_command()
        self.assertEqual(result["eligible_labelled_adults"], 4)
        self.assertEqual(result["undetermined_assignments"], 1)
        self.assertEqual(result["exclusions"], {
            "missing_age": 1, "invalid_age": 8, "under_18": 2,
            "missing_target": 1, "unusable_target": 2,
        })
        self.assertEqual(result["matched_records"],
                         sum(result["exclusions"].values()) + result["eligible_labelled_adults"])

    def test_missing_tokens_match_exactly_and_do_not_normalize_labels(self):
        self.config["missing_tokens"]["age"].append("999")
        self.config["missing_tokens"]["target"].append("MISSING")
        self.save_config()
        targets = ["MISSING", " MISSING", "missing", "Invented A", "Invented A ",
                   "Undetermined", "undetermined", "Undetermined ", "Invented A"]
        self.prepare([{"IIntID": f"INVENTED-{i}", "Age_in_years": "999" if i == 8 else "18",
                       "cause1_InterVA": target} for i, target in enumerate(targets)])
        result = self.run_command()
        self.assertEqual(result["exclusions"]["missing_target"], 1)
        self.assertEqual(result["exclusions"]["missing_age"], 1)
        self.assertEqual(result["eligible_labelled_adults"], 7)
        self.assertEqual(result["distinct_target_classes"], 7)
        self.assertEqual(result["undetermined_assignments"], 1)

    def test_exact_identifiers_preserve_zeros_large_digits_and_whitespace(self):
        keys = ["001", "1", "9007199254740992", "9007199254740993", "1.0", "1e0", " 1"]
        deaths = [{"IIntID": key, "Age_in_years": "18", "cause1_InterVA": "Invented A"}
                  for key in keys]
        indicators = [{"IIntID": key} for key in reversed(keys[:-1])]
        self.prepare(deaths, indicators)
        result = self.run_command()
        self.assertEqual(result["eligible_labelled_adults"], 6)
        self.assertEqual(result["inputs"]["deaths"]["unmatched"], 1)

    def test_missing_keys_and_orphans_are_excluded_before_eligibility(self):
        self.config["missing_tokens"]["identifier"].append("MISSING")
        self.save_config()
        keys = ["MATCH", "DEATHS-ONLY", "", "", "MISSING"]
        self.prepare(
            [{"IIntID": key, "Age_in_years": "18" if key == "MATCH" else "",
              "cause1_InterVA": "Invented A"} for key in keys],
            [{"IIntID": key} for key in ("MATCH", "INDICATORS-ONLY", "", "MISSING", " MISSING")],
        )
        result = self.run_command()
        self.assertEqual(result["matched_records"], 1)
        self.assertEqual(result["exclusions"]["missing_age"], 0)
        self.assertEqual(result["inputs"], {
            "deaths": {"rows": 5, "missing_identifiers": 3, "unmatched": 1},
            "indicators": {"rows": 5, "missing_identifiers": 2, "unmatched": 2},
        })
        for counts in result["inputs"].values():
            self.assertEqual(counts["rows"], counts["missing_identifiers"] + counts["unmatched"]
                             + result["matched_records"])

    def test_duplicate_keys_fail_even_with_identical_targets_or_without_matches(self):
        for role in ("deaths", "indicators"):
            with self.subTest(role=role):
                self.prepare()
                row = {"IIntID": "SENSITIVE-INVENTED-ORPHAN"}
                if role == "deaths":
                    row.update(Age_in_years="", cause1_InterVA="Invented A")
                self.table(role, [row, row])
                errors = " ".join(self.run_command(2)["errors"])
                self.assertIn(f"{role}.IIntID", errors)
                self.assertIn("duplicate_identifier_groups=1", errors)
                self.assertIn("duplicate_identifier_rows=2", errors)

    def test_conflicting_targets_fail_without_echoing_key_or_labels(self):
        self.prepare([
            {"IIntID": "SENSITIVE-INVENTED-KEY", "Age_in_years": "18",
             "cause1_InterVA": "SENSITIVE-INVENTED-A"},
            {"IIntID": "SENSITIVE-INVENTED-KEY", "Age_in_years": "18",
             "cause1_InterVA": "SENSITIVE-INVENTED-B"},
        ], [{"IIntID": "SENSITIVE-INVENTED-KEY"}])
        self.assertIn("conflicting_target_identifiers=1", " ".join(self.run_command(2)["errors"]))

    def test_unusable_identifier_fails_without_guessing_normalization(self):
        for key in (" \t ", "SENSITIVE-INVENTED\x00KEY"):
            with self.subTest(key=key):
                self.prepare([{"IIntID": key, "Age_in_years": "18", "cause1_InterVA": "Invented A"}])
                self.assertIn("unusable_identifiers=1", " ".join(self.run_command(2)["errors"]))

    def test_all_three_indicator_states_remain_distinct(self):
        self.table("indicators", [{"IIntID": "INVENTED-001", "i004a": "y", "i004b": "n"}])
        self.assertEqual(self.run_command()["eligible_indicator_states"], {"y": 1, "n": 1, "-": 351})

    def test_invalid_indicator_cells_fail_even_on_excluded_or_unmatched_records(self):
        for code in ("SENSITIVE-INVENTED-CODE", "Y", " n", "NA", "", "--"):
            with self.subTest(code=code):
                self.table("indicators", [
                    {"IIntID": "INVENTED-001", "i004a": code},
                    {"IIntID": "ORPHAN", "i004a": code},
                    {"IIntID": "", "i004a": code},
                ])
                self.assertIn("indicators.i004a: undeclared_values=3",
                              " ".join(self.run_command(2)["errors"]))

    def test_blank_mapping_requires_explicit_review_and_maps_only_to_missing(self):
        self.table("indicators", [{"IIntID": "INVENTED-001", "i004a": ""}])
        self.run_command(2)
        self.config["indicator_blank_mapping"] = "missing_inapplicable"
        self.save_config()
        self.assertIn("indicator_blank_mapping_reviewed", " ".join(self.run_command(2)["errors"]))
        self.config["indicator_blank_mapping_reviewed"] = True
        self.save_config()
        self.assertEqual(self.run_command()["eligible_indicator_states"], {"y": 0, "n": 0, "-": 353})
        self.table("indicators", [{"IIntID": "INVENTED-001", "i004a": " "}])
        self.run_command(2)

    def test_feature_allowlist_excludes_all_extras_and_cannot_be_overridden(self):
        baseline = self.run_command()
        extras = [name for name in SCHEMA["indicators"] if name not in PREDICTORS and name != "IIntID"]
        self.assertEqual(len(extras), 5)
        extras += [name for name in SCHEMA["deaths"] if name != "IIntID"]
        extras += ["iINVENTED_extra"]  # An i-prefix must not make a predictor.
        for value in ("SENSITIVE-INVENTED-EXTRA", "", "y"):
            with self.subTest(value=value):
                row = dict.fromkeys(extras, value)
                row["IIntID"] = "INVENTED-001"
                self.table("indicators", [row], [*extras, *reversed(PREDICTORS), "IIntID"])
                self.table("deaths", [{"IIntID": "INVENTED-001", "Age_in_years": "18",
                                       "cause1_InterVA": "Invented cause A",
                                       "Questionnaire": value, "cause2_InterVA": value}],
                           ["cause2_InterVA", "IIntID", "Questionnaire", "cause1_InterVA", "Age_in_years"])
                self.assertEqual(self.run_command(), baseline)
        self.config["predictors"] = ["cause1_InterVA"]
        self.save_config()
        self.run_command(2)

    def test_missing_columns_report_only_known_field_names(self):
        cases = [("deaths", "Age_in_years"), ("deaths", "cause1_InterVA"),
                 ("deaths", "IIntID"), ("indicators", "IIntID"), ("indicators", PREDICTORS[-1])]
        for role, missing in cases:
            with self.subTest(role=role, missing=missing):
                self.prepare()
                fields = (["IIntID", "Age_in_years", "cause1_InterVA"] if role == "deaths"
                          else ["IIntID", *PREDICTORS])
                self.table(role, [], [field for field in fields if field != missing]
                           + ["SENSITIVE-INVENTED-HEADER"])
                self.assertIn(missing, " ".join(self.run_command(2)["errors"]))

    def test_blank_duplicate_and_absent_headers_fail_without_echo(self):
        for header in ("", "IIntID,,Age_in_years,cause1_InterVA\n",
                       "IIntID,Age_in_years,cause1_InterVA,SENSITIVE-INVENTED,SENSITIVE-INVENTED\n"):
            with self.subTest(header=header):
                (self.work / "deaths.csv").write_text(header, encoding="utf-8")
                self.run_command(2)

    def test_malformed_csv_and_invalid_utf8_are_value_free_failures(self):
        header = b"IIntID,Age_in_years,cause1_InterVA\n"
        cases = [b'SENSITIVE-INVENTED,18,"UNCLOSED', b'SENSITIVE-INVENTED,18,"A"oops\n',
                 b'SENSITIVE-INVENTED"KEY,18,A\n',
                 b"SENSITIVE-INVENTED,18\n", b"SENSITIVE-INVENTED,18,A,extra\n", b"\n",
                 b"SENSITIVE-INVENTED,18,\xff\n", b"SENSITIVE-INVENTED,18," + b"X" * 131073]
        for body in cases:
            with self.subTest(body=body[:60]):
                (self.work / "deaths.csv").write_bytes(header + body)
                self.assertIn("malformed_records", " ".join(self.run_command(2)["errors"]))

    def test_csv_quoted_comma_quotes_unicode_and_crlf_are_supported(self):
        labels = ['Invented "A", B', "Invented cause café"]
        self.prepare([{"IIntID": f"INVENTED-{i}", "Age_in_years": "18", "cause1_InterVA": label}
                      for i, label in enumerate(labels)])
        result = self.run_command()
        self.assertEqual(result["distinct_target_classes"], 2)
        self.assertEqual(result["eligible_labelled_adults"], 2)

    def test_quoted_multiline_metadata_is_parsed_but_never_becomes_a_feature(self):
        self.table("indicators", [{"IIntID": "INVENTED-001", "notes": 'Invented\r\n"note",\ntext'}],
                   ["IIntID", "notes", *PREDICTORS])
        self.assertEqual(self.run_command()["eligible_labelled_adults"], 1)

    def test_byte_order_mark_is_rejected_with_an_actionable_diagnostic(self):
        path = self.work / "deaths.csv"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertIn("UTF-8 without BOM", " ".join(self.run_command(2)["errors"]))

    def test_empty_tables_and_no_eligible_adults_do_not_claim_feasibility(self):
        for rows in ([], [{"IIntID": "INVENTED-CHILD", "Age_in_years": "17", "cause1_InterVA": "A"}]):
            with self.subTest(rows=rows):
                self.prepare(rows)
                result = self.run_command()
                self.assertEqual(result["eligible_labelled_adults"], 0)
                self.assertEqual(result["benchmark_feasibility"], "infeasible")

    def test_invalid_configuration_fails_before_opening_inputs(self):
        original = self.config
        cases = [None, [], {}, {**original, "schema_version": True},
                 {**original, "identifier_normalization": "numeric"},
                 {**original, "age_semantics": "age_at_interview"},
                 {**original, "undetermined_label": "SENSITIVE-INVENTED"},
                 {**original, "indicator_blank_mapping": "n"},
                 {**original, "indicator_blank_mapping_reviewed": "true"},
                 {**original, "missing_tokens": None},
                 {**original, "SENSITIVE-INVENTED": "value"}]
        for tokens in ([], ["", 1], ["", {}], ["", ""], ["", "Undetermined"], ""):
            cases.append({**original, "missing_tokens": {**original["missing_tokens"], "target": tokens}})
        for key, value in (("encoding", "latin-1"), ("delimiter", "tab"), ("escape", "backslash"),
                           ("doublequote", 1), ("header_row", True), ("header_row", 2)):
            cases.append({**original, "serialization": {**original["serialization"], key: value}})
        (self.work / "deaths.csv").unlink()
        for config in cases:
            with self.subTest(config=config):
                self.config = config
                self.save_config()
                self.assertNotIn("cannot read input", " ".join(self.run_command(2)["errors"]))

    def test_unreadable_or_malformed_config_and_duplicate_json_keys_fail(self):
        for content in ('{"SENSITIVE-INVENTED":', '{"schema_version":1,"schema_version":1}',
                        '[NaN]', '[' * 2000, '\ufeff{}'):
            with self.subTest(content=content[:30]):
                (self.work / "config.json").write_text(content, encoding="utf-8")
                self.run_command(2)
        (self.work / "config.json").unlink()
        self.run_command(2)

    def test_unreadable_input_and_bad_arguments_do_not_echo_paths(self):
        (self.work / "indicators.csv").unlink()
        self.assertIn("indicators", " ".join(self.run_command(2)["errors"]))
        for argv in ([], ["SENSITIVE-INVENTED"], ["validate", "--deaths", "SENSITIVE-INVENTED"],
                     ["validate", "--SENSITIVE-INVENTED"]):
            self.run_command(2, argv=argv)

    def test_module_entrypoint_works_in_a_fresh_process(self):
        result = subprocess.run(
            [sys.executable, "-m", "ahri_va", "validate", "--deaths", str(self.work / "deaths.csv"),
             "--indicators", str(self.work / "indicators.csv"), "--config", str(self.work / "config.json")],
            cwd=ROOT / "src", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["summary"]["eligible_labelled_adults"], 1)


if __name__ == "__main__":
    unittest.main()
