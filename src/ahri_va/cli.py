"""Public commands: aggregate validation JSON or the baseline Markdown report."""

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys

from ahri_va.config import load_configuration, ValidationError
from ahri_va.population import retain_classes
from ahri_va.partitions import make_partitions
from ahri_va.validation import validate_inputs


__all__ = ["main"]


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes supplied arguments, potentially private paths.
        raise ValidationError(
            "command: require validate or benchmark with --deaths FILE --indicators FILE --config FILE; "
            "use --help for usage."
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run validate or benchmark; return 0 on success and 2 on failure.

    Args:
        argv: Command arguments, or None to use the process arguments.

    Returns:
        Validation writes aggregate JSON to stdout without fitting models.
        Benchmark writes aggregate Markdown. Failure writes JSON to stderr;
        errors omit record values, with aggregate class counts where available.
        No output files are created by either command.
    """
    parser = _Parser(prog="ahri-va", description="Validate and baseline adult InterVA5 replication.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("validate", "Check inputs, adult eligibility, population and partitions without fitting."),
        ("benchmark", "Check feasibility and print a baseline Markdown report."),
    ):
        subcommand = commands.add_parser(command, help=help_text)
        subcommand.add_argument("--deaths", type=Path, required=True)
        subcommand.add_argument("--indicators", type=Path, required=True)
        subcommand.add_argument("--config", type=Path, required=True)
    summary: dict[str, object] = {}
    try:
        args = parser.parse_args(argv)
        config = load_configuration(args.config)
        eligible = validate_inputs(args.deaths, args.indicators, config)
        population = retain_classes(eligible)
        summary = {**eligible.summary, "population": population.summary(),
                   "scope": "input_eligibility_population_and_partitions",
                   "benchmark_feasibility": "infeasible"}
        if len(population.retained_classes) < 2:
            raise ValidationError(
                "population: require at least two retained classes with five eligible labelled "
                f"adults each; retained_classes={len(population.retained_classes)}."
            )
        plan = make_partitions(population)
        summary["partitions"] = plan.summary(population)
        summary["benchmark_feasibility"] = "feasible"
        if args.command == "benchmark":
            from ahri_va.baseline import evaluate_baseline
            from ahri_va.report import baseline_report

            summary.pop("models_fitted")
            result = evaluate_baseline(population, plan)
            report = baseline_report(eligible, population, plan, result)
    except ValidationError as error:
        failure: dict[str, object] = {"status": "failed", "errors": str(error).splitlines()}
        if summary:
            summary["status"] = "failed"
            failure["summary"] = summary
        print(json.dumps(failure), file=sys.stderr)
        return 2
    if args.command == "benchmark":
        print(report, end="")
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
