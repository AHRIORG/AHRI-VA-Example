"""Generate teaching CSVs from fictional records only; never open participant data."""

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    """Write invented inputs into a new directory, without overwriting files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    predictors = json.loads((root / "scripts/documented-schema.json").read_text())["predictors"]
    records = [
        ("0001", "18", "Invented cause A"),
        ("1", "42", "Invented cause B"),
        ("9007199254740993", "65", "Undetermined"),
        ("INVENTED-CHILD", "17", "Invented cause A"),
        ("INVENTED-MISSING-AGE", "", "Invented cause A"),
        ("INVENTED-INVALID-AGE", "18.5", "Invented cause A"),
        ("INVENTED-MISSING-TARGET", "23", ""),
        ("INVENTED-UNUSABLE-TARGET", "24", "  "),
    ]
    # Five eligible records in each retained class, plus four in an excluded
    # class. The eligibility exclusions above still each contribute one record.
    records.extend((f"INVENTED-RETAINED-{group}-{i}", "40", label)
                   for group, label in enumerate(("Invented cause A", "Invented cause B", "Undetermined"))
                   for i in range(4))
    records.extend((f"INVENTED-RARE-{i}", "50", "Invented rare cause") for i in range(4))
    with (args.output_dir / "deaths.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["IIntID", "Age_in_years", "cause1_InterVA"])
        writer.writerows(records)
        writer.writerow(["INVENTED-DEATHS-ONLY", "50", "Invented cause B"])
        writer.writerow(["", "50", "Invented cause B"])
    with (args.output_dir / "indicators.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["IIntID", *predictors])
        for identifier, _, _ in records:
            writer.writerow([identifier, "y", "n", *(["-"] * (len(predictors) - 2))])
        writer.writerow(["INVENTED-INDICATORS-ONLY", *(["-"] * len(predictors))])
        writer.writerow(["", *(["-"] * len(predictors))])
    print("Wrote invented deaths.csv and indicators.csv; eligible adults: 19; retained: 15.")


if __name__ == "__main__":
    main()
