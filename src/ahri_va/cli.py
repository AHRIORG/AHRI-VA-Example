"""Public command boundary; diagnostics contain no paths or record values."""

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys

from ahri_va.config import load_configuration, ValidationError
from ahri_va.validation import validate_inputs


__all__ = ["main"]


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes supplied arguments, potentially private paths.
        raise ValidationError(
            "command: require validate --deaths FILE --indicators FILE --config FILE; "
            "use --help for usage."
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Run validate; return 0 for valid input/eligibility and 2 for failure.

    Args:
        argv: Command arguments, or None to use the process arguments.

    Returns:
        Exit status. Success writes aggregate JSON to stdout; failure writes
        value-free JSON diagnostics to stderr. No output files are created.
    """
    parser = _Parser(prog="ahri-va", description="Validate adult InterVA5 replication inputs.")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Check inputs and adult/label eligibility.")
    validate.add_argument("--deaths", type=Path, required=True)
    validate.add_argument("--indicators", type=Path, required=True)
    validate.add_argument("--config", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        config = load_configuration(args.config)
        eligible = validate_inputs(args.deaths, args.indicators, config)
    except ValidationError as error:
        print(json.dumps({"status": "failed", "errors": str(error).splitlines()}), file=sys.stderr)
        return 2
    print(json.dumps(eligible.summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
