#!/usr/bin/env python3
"""Build a source-only, offline Ticket 01 handoff from an explicit file allowlist."""

import argparse
import gzip
import hashlib
import io
from pathlib import Path
import re
import tarfile


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md", "CONTEXT.md",
    "scripts/input_evidence.py", "scripts/private-input-wizard.sh",
    "scripts/documented-schema.json", "scripts/build_transfer_bundle.py",
    "tests/test_input_evidence.py",
    "docs/private-input-evidence.md", "docs/input-spec-review.md", "docs/design-interview.md",
    "docs/data_specs/AHRI.VerbalAutopsy.Harmonisation.json",
    "docs/data_specs/VerbalAutopsy.Harmonisation_Data.pdf",
    "docs/adr/0001-replicate-interva5-first-cause.md",
    "docs/adr/0002-exclude-infeasible-cause-classes.md",
    "docs/agents/domain.md", "docs/agents/issue-tracker.md", "docs/agents/triage-labels.md",
    "docs/issues/interva5-replication/spec.md",
    "docs/issues/interva5-replication/issues/01-private-input-evidence-wizard.md",
    "docs/issues/interva5-replication/issues/02-validate-inputs-and-adult-eligibility.md",
    "docs/issues/interva5-replication/issues/03-baseline-and-partition-checks.md",
    "docs/issues/interva5-replication/issues/04-logistic-regression-selection.md",
    "docs/issues/interva5-replication/issues/05-random-forest-and-complete-report.md",
    "AGENTS.md",
)

START_HERE = """# Ticket 01 private transfer bundle

This archive contains source, documentation and tests that generate invented
teaching fixtures. It contains no private inputs or evidence.

Prerequisites confirmed by the user: the same Mac, with Bash and Python 3.11+.
No network access, pip packages, installation, Git or agent is needed to run it.
An interpreter is not bundled because one is already available in that account.

1. Extract this archive into a private directory in the analysis account.
2. In Terminal, change into the extracted `ahri-va-ticket01` directory.
3. Verify contents if desired: `shasum -a 256 -c SHA256SUMS`.
4. Check `python3 --version` and `bash --version`.
5. Optional invented-only self-check: `python3 -m unittest discover -s tests -v`.
6. Read [the guide](docs/private-input-evidence.md), then run:

   ```bash
   bash scripts/private-input-wizard.sh /absolute/private/new-evidence-directory
   ```

The parent of that new directory must exist. Set `PYTHON_RUNTIME` to another
installed Python executable if necessary, as described in the guide.

Only you run actual-input commands. Never launch an agent in the analysis
account. The wizard uses your offline editor; it does not open browsers, install
readers, convert files, fit models, upload or commit anything. Unsupported native
formats remain explicit preparation questions.

After local review, manually transfer only your approved summary. Ticket 01 is
not complete until that handoff; unresolved input-contract questions block
Ticket 02. All working evidence stays private. The guide gives the destination
and explains the capture/release choices.
"""


def build(output: Path, revision: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Supply the full reviewed source commit SHA.")
    payloads = {name: (ROOT / name).read_bytes() for name in FILES}
    payloads["START-HERE.md"] = START_HERE.encode()
    payloads["BUNDLE-INFO.txt"] = (
        f"Source commit: {revision}\n"
        "Runtime: Bash; Python >=3.11 standard library only.\n"
        "Development verification: invented fixtures only; no interactive wizard execution.\n"
        "Private evidence: not included; human execution and review still required.\n"
    ).encode()
    payloads["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(contents).hexdigest()}  {name}\n"
        for name, contents in sorted(payloads.items())
    ).encode()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, contents in sorted(payloads.items()):
            info = tarfile.TarInfo("ahri-va-ticket01/" + name)
            info.size = len(contents)
            info.mode = 0o755 if name == "scripts/private-input-wizard.sh" else 0o644
            archive.addfile(info, io.BytesIO(contents))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{checksum}  {output.name}\n")
    print(f"Built source-only archive with {len(payloads)} files.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    build(args.output, args.revision)


if __name__ == "__main__":
    main()
