"""Public-command checks using invented teaching records only."""

import csv
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts/input_evidence.py"
SCHEMA = json.loads((ROOT / "scripts/documented-schema.json").read_text())


class EvidenceCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / "evidence"

    def run_command(self, command, expected=0):
        result = subprocess.run(
            [sys.executable, str(COMMAND), command, "--work-dir", str(self.work)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def save(self, name, value):
        (self.work / name).write_text(json.dumps(value), encoding="utf-8")

    def load(self, name):
        return json.loads((self.work / name).read_text())

    def fixture(self, role, records):
        fields = SCHEMA[role]
        path = Path(self.temp.name) / (role + ".csv")
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for record in records:
                row = dict.fromkeys(fields, "-")
                row.update(record)
                writer.writerow(row)
        return {
            "path": str(path), "role": role, "format": "delimited",
            "table_organisation": "single_table", "private_release_evidence": "",
            "serialization": {
                "encoding": "utf-8", "delimiter": "comma", "quote": "double",
                "escape": "none", "doublequote": True, "header_row": 1,
            },
        }

    def prepare(self, deaths=None, indicators=None):
        self.run_command("init")
        self.save("inventory.json", {"files": [
            self.fixture("deaths", deaths or [
                {"IIntID": "00071", "Age_in_years": "18", "cause1_InterVA": "Invented cause A"},
            ]),
            self.fixture("indicators", indicators or [{"IIntID": "00071", "i004a": "y"}]),
        ], "missing_tokens": {"identifier": None, "age": None, "target": None},
            "indicator_blank_mapping": "unresolved"})

    def test_inspection_reports_documentary_matches_without_confirming_meaning(self):
        self.prepare()
        self.run_command("inspect")
        observed = self.load("observations.json")
        self.assertEqual(observed["inputs"][0]["counts"]["rows"], 1)
        self.assertEqual(observed["inputs"][1]["schema"]["predictors_present"], 353)
        self.assertEqual(observed["linkage"]["matched_unique_identifiers"], 1)
        self.assertEqual(observed["inputs"][0]["counts"]["declared_missing_targets"], None)
        self.assertEqual(self.load("review.json")["age_at_death"]["status"], "unresolved")

    def test_integrity_findings_preserve_exact_keys_and_never_repair_conflicts(self):
        self.prepare(deaths=[
            {"IIntID": "00071", "Age_in_years": "18", "cause1_InterVA": "Invented A"},
            {"IIntID": "71", "Age_in_years": "17", "cause1_InterVA": "Invented B"},
            {"IIntID": "9007199254740993", "Age_in_years": "18.5", "cause1_InterVA": "Invented C"},
            {"IIntID": "9007199254740992", "Age_in_years": "NaN", "cause1_InterVA": "Invented C"},
            {"IIntID": "DUPLICATE", "Age_in_years": "", "cause1_InterVA": "Invented A"},
            {"IIntID": "DUPLICATE", "Age_in_years": "998", "cause1_InterVA": "Invented B"},
            {"IIntID": "", "Age_in_years": "-1", "cause1_InterVA": "MISSING"},
        ], indicators=[
            {"IIntID": "00071", "i004a": "y", "i004b": "n", "i019a": ""},
            {"IIntID": "9007199254740993", "i004a": "UNEXPECTED-PRIVATE-VALUE"},
            {"IIntID": "UNMATCHED"},
        ])
        config = self.load("inventory.json")
        config["missing_tokens"] = {"identifier": [""], "age": ["", "998"], "target": ["", "MISSING"]}
        self.save("inventory.json", config)
        self.run_command("inspect")
        observed = self.load("observations.json")
        deaths, indicators = [t["counts"] for t in observed["inputs"]]
        self.assertEqual(deaths["duplicate_identifier_groups"], 1)
        self.assertEqual(deaths["conflicting_target_identifiers"], 1)
        self.assertEqual(deaths["blank_identifiers"], 1)
        self.assertEqual(deaths["declared_missing_targets"], 1)
        self.assertEqual(deaths["declared_missing_ages"], 2)
        self.assertEqual(deaths["non_completed_year_number_ages"], 3)
        self.assertEqual(deaths["leading_zero_identifiers"], 1)
        self.assertEqual(deaths["large_digit_identifiers"], 2)
        self.assertEqual(indicators["indicator_y"], 1)
        self.assertEqual(indicators["indicator_n"], 1)
        self.assertEqual(indicators["indicator_blank"], 1)
        self.assertEqual(indicators["indicator_unexpected"], 1)
        self.assertEqual(observed["linkage"]["matched_unique_identifiers"], 2)
        self.assertEqual(observed["linkage"]["deaths_only_identifiers"], 3)
        self.assertEqual(observed["linkage"]["indicators_only_identifiers"], 1)
        self.assertFalse(observed["linkage"]["one_to_one"])
        self.assertNotIn("UNEXPECTED-PRIVATE-VALUE", json.dumps(observed))

    def test_native_inventory_handles_many_files_and_marks_unsupported_formats(self):
        self.prepare()
        config = self.load("inventory.json")
        source = Path(config["files"][1]["path"])
        compressed = source.with_suffix(".csv.gz")
        compressed.write_bytes(gzip.compress(source.read_bytes()))
        config["files"][1]["path"] = str(compressed)
        unsupported = Path(self.temp.name) / "private-workbook.xlsx"
        unsupported.write_bytes(b"PK\x03\x04invented unsupported workbook")
        config["files"].append({"path": str(unsupported), "role": "other", "format": "xlsx",
                                "table_organisation": "multiple_sheets"})
        self.save("inventory.json", config)
        self.run_command("inventory")
        inventory = self.load("inventory-observations.json")
        self.assertEqual(len(inventory["inputs"]), 3)
        self.assertEqual(inventory["inputs"][1]["observed_container"], "gzip")
        self.assertEqual(inventory["inputs"][2]["observed_container"], "zip")
        self.run_command("inspect")
        observed = self.load("observations.json")
        self.assertEqual(observed["inputs"][1]["counts"]["rows"], 1)
        self.assertEqual(observed["inputs"][2]["status"], "unsupported")
        self.assertNotIn("private-workbook", json.dumps(observed))

    def test_candidate_is_an_allowlisted_projection_with_explicit_release_choices(self):
        self.prepare()
        config = self.load("inventory.json")
        config["files"][0]["private_release_evidence"] = "PRIVATE-CONTRACT-LOCATION"
        self.save("inventory.json", config)
        self.run_command("inspect")
        review = self.load("review.json")
        review["age_at_death"].update(
            status="user_confirmed", private_evidence="PRIVATE-REPORT-DETAILS",
            release_statement="Age denotes completed years at death.", release_approved=True,
        )
        review["preparation"]["release_statement"] = "UNAPPROVED-FREE-TEXT"
        review["release_sections"] = {"inventory": True, "serialization": True, "schema": True, "characteristics": True}
        self.save("review.json", review)
        self.run_command("summary")
        summary = (self.work / "candidate-summary.md").read_text()
        self.assertIn("Age denotes completed years at death.", summary)
        self.assertIn("353", summary)
        self.assertIn("unresolved", summary)
        self.assertIn("Ticket 02 remains blocked", summary)
        for private in (self.temp.name, "PRIVATE-CONTRACT-LOCATION", "PRIVATE-REPORT-DETAILS",
                        "UNAPPROVED-FREE-TEXT", "00071", "Invented cause A"):
            self.assertNotIn(private, summary)
        review["release_sections"]["characteristics"] = False
        self.save("review.json", review)
        self.run_command("summary")
        self.assertNotIn("matched_unique_identifiers", (self.work / "candidate-summary.md").read_text())

    def test_malformed_records_invalidate_old_drafts_and_return_value_free_diagnostics(self):
        self.prepare()
        self.run_command("inspect")
        self.run_command("summary")
        config = self.load("inventory.json")
        Path(config["files"][0]["path"]).write_text(
            'IIntID,Age_in_years,cause1_InterVA\nPRIVATE-RECORD,18,"PRIVATE-UNCLOSED', encoding="utf-8")
        result = self.run_command("inspect", expected=2)
        self.assertNotIn("PRIVATE-", result.stdout + result.stderr)
        self.assertNotIn(self.temp.name, result.stdout + result.stderr)
        self.assertFalse((self.work / "candidate-summary.md").exists())
        self.assertEqual(self.load("observations.json")["inputs"][0]["status"], "unreadable_or_malformed")
        self.run_command("summary")
        summary = (self.work / "candidate-summary.md").read_text()
        self.assertNotIn("PRIVATE-", summary)
        self.assertIn("inspection is unsupported or incomplete", summary)

    def test_unknown_serialization_stays_unresolved_instead_of_being_guessed(self):
        self.prepare()
        config = self.load("inventory.json")
        config["files"][0]["serialization"] = None
        self.save("inventory.json", config)
        self.run_command("inspect")
        observed = self.load("observations.json")
        self.assertEqual(observed["inputs"][0]["status"], "serialization_unresolved")
        self.assertEqual(observed["linkage"]["status"], "unresolved")
        self.run_command("summary")

    def test_missing_columns_are_unavailable_not_zero_and_extra_names_are_omitted(self):
        self.prepare()
        config = self.load("inventory.json")
        Path(config["files"][0]["path"]).write_text(
            "PRIVATE-HEADER,Age_in_years\nPRIVATE-RECORD,18\n", encoding="utf-8")
        self.run_command("inspect")
        observed = self.load("observations.json")
        self.assertEqual(observed["inputs"][0]["schema"]["missing_required_fields"], ["IIntID", "cause1_InterVA"])
        self.assertIsNone(observed["inputs"][0]["counts"]["blank_identifiers"])
        self.assertIsNone(observed["inputs"][0]["counts"]["indicator_y"])
        self.assertEqual(observed["linkage"]["status"], "unresolved")
        self.assertNotIn("PRIVATE-", json.dumps(observed))

    def test_declared_dialect_supports_preamble_quoted_delimiters_and_literal_nulls(self):
        self.prepare()
        config = self.load("inventory.json")
        Path(config["files"][0]["path"]).write_bytes(
            'Export metadata\nIIntID;Age_in_years;cause1_InterVA\n00071;18;"Invented; Caf\u00e9"\nSECOND;.;NULL\n'.encode("cp1252"))
        config["files"][0]["serialization"].update(encoding="cp1252", delimiter="semicolon", header_row=2)
        config["missing_tokens"] = {"identifier": [""], "age": ["", "."], "target": ["", "NULL"]}
        self.save("inventory.json", config)
        self.run_command("inspect")
        counts = self.load("observations.json")["inputs"][0]["counts"]
        self.assertEqual(counts["rows"], 2)
        self.assertEqual(counts["declared_missing_ages"], 1)
        self.assertEqual(counts["declared_missing_targets"], 1)
        self.assertEqual(counts["non_completed_year_number_ages"], 0)

    def test_changed_configuration_prevents_releasing_stale_observations(self):
        self.prepare()
        self.run_command("inspect")
        self.run_command("summary")
        config = self.load("inventory.json")
        config["indicator_blank_mapping"] = "reject"
        self.save("inventory.json", config)
        result = self.run_command("summary", expected=2)
        self.assertIn("rerun inspect", result.stdout)
        self.assertFalse((self.work / "candidate-summary.md").exists())

    def test_parser_failures_never_emit_record_values_or_tracebacks(self):
        self.prepare()
        config = self.load("inventory.json")
        path = Path(config["files"][0]["path"])
        for malformed in (
            b"IIntID,Age_in_years,cause1_InterVA\nPRIVATE,18,Cause,EXTRA\n",
            b"IIntID,IIntID\nPRIVATE,PRIVATE\n",
            b"IIntID,Age_in_years,cause1_InterVA\nPRIVATE,18,\xff\n",
            b"\x1f\x8bPRIVATE-CORRUPT-GZIP",
            b"",
        ):
            with self.subTest(input=malformed[:8]):
                path.write_bytes(malformed)
                result = self.run_command("inspect", expected=2)
                self.assertNotIn("PRIVATE", result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                self.assertEqual(self.load("observations.json")["inputs"][0]["status"], "unreadable_or_malformed")

    def test_malformed_configuration_and_unapproved_notes_are_not_diagnostics(self):
        self.prepare()
        (self.work / "inventory.json").write_text('{"PRIVATE-CONFIG": invalid}')
        result = self.run_command("inspect", expected=2)
        self.assertNotIn("PRIVATE-CONFIG", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
