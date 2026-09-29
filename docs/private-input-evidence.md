# Private input-evidence wizard

Ticket 01 provides tooling for a human evidence review. It does not validate a
benchmark population or fit a model. Only the user runs it with actual inputs,
in the separate analysis account. Never run an agent in that account or bring
private evidence into this development account.

The transfer bundle is self-contained given the confirmed prerequisites: Bash
and Python 3.11 or newer on the same Mac. It needs no network, pip installation,
third-party Python packages or native-format readers. The source checkout has
the same runtime requirements. ShellCheck and mypy are development tools, not
private-execution prerequisites.

## Start privately

1. Transfer the archive to the analysis account by your approved local method.
   Extract it into a private directory. Do not extract over an earlier run.
2. In Terminal, change into the extracted `ahri-va-ticket01` directory.
3. Confirm prerequisites with `bash --version` and `python3 --version`. If the
   latter is older than 3.11, use an already available interpreter's absolute
   path as `PYTHON_RUNTIME` below. Do not install anything based on an assumed
   native data format.
4. Optionally run the bundled invented-fixture checks before touching inputs:

   ```bash
   python3 -m unittest discover -s tests -v
   bash -n scripts/private-input-wizard.sh
   ```

5. Launch the wizard, choosing a **new absolute directory** under a private
   parent directory that already exists:

   ```bash
   bash scripts/private-input-wizard.sh /absolute/private/input-evidence
   ```

   To select a different installed interpreter:

   ```bash
   PYTHON_RUNTIME=/absolute/path/to/python3 bash scripts/private-input-wizard.sh /absolute/private/input-evidence
   ```

Use an offline text editor for JSON and Markdown. The wizard supplies paths and
confirmation gates; it does not launch an editor or send anything over the
network. Allow approximately 45 minutes, plus any investigation/conversion of
unsupported inputs. Ctrl-C stops the procedure. Rerun with the same directory
to revisit the stages with saved JSON; answers are not silently loaded as shell
code. Inspection regenerates observations and invalidates an earlier draft.

The Python commands below are also available for correcting one stage. Replace
the example working directory with your private directory and use your chosen
Python executable consistently:

```bash
python3 scripts/input_evidence.py inventory --work-dir /absolute/private/input-evidence
python3 scripts/input_evidence.py inspect --work-dir /absolute/private/input-evidence
python3 scripts/input_evidence.py summary --work-dir /absolute/private/input-evidence
```

`init --work-dir ...` initializes a new directory; it refuses an existing one.
Commands exit 2 for invalid configuration or unreadable/malformed inputs and
use fixed diagnostics without record values. Unsupported formats and unknown
serialization are recorded as unresolved findings; exit 0 means evidence was
collected, **not that inputs are suitable**. Review the observation statuses.

## Capture and destination map

This plan and the Python command testing boundary were confirmed by the user.
Every file below remains private until the user manually approves a release.

| Stage | Captured values and source | Private destination | Eligible for deliberate release |
| --- | --- | --- | --- |
| 1. Inventory, 8 min | User's local file inventory: paths, role, native format, table/sheet organisation and release/version evidence; interpreter version and Python signature checks | `inventory.json`, `inventory-observations.json`; runtime/location references and stage confirmations in `wizard.env` | Selected counts, format/organisation declarations, observed compression container and separately approved version statement |
| 2. Serialization, 7 min | Export/native documentation and private user checks: encoding, delimiter, quote/escape rules, header record, blank/null serialization | `inventory.json`; observations of parsing in `observations.json` | Selected parsing declarations; meanings require separate confirmation |
| 3. Schema, 5 min | Python compares headers with the shipped documentary names; user checks private v2 evidence | `observations.json`; `review.json` topic `v2_compatibility` | Expected-field names, aggregate schema differences, approved compatibility statement |
| 4. Characteristics, 10 min | Python aggregate checks; private provenance for identifiers, completed age at death, missing and undetermined conventions | `observations.json`; `inventory.json` exact missing tokens; four corresponding `review.json` topics | Selected aggregate counts and separately approved convention statements |
| 5. Preparation, 10 min | User's conversion/mapping decisions and unresolved questions from private evidence | `review.json` topic `preparation` | Only its explicitly approved release statement |
| 6. Review, 5 min | User's section choices, topic status, separate release wording and explicit approval flags | `review.json`; separate `candidate-summary.md` | Only the final manually reviewed summary, never the working directory |

`wizard.env` contains paths and progress acknowledgements, not data or scientific
verification. Python reads JSON, never sources the environment file. The wizard
uses owner-only creation permissions and keeps its temporary environment edits
in the working directory. Account separation, directory access permissions and
your release process provide the access boundary; instructions and Git ignores
are not access controls. Do not enable shell tracing or record terminal sessions.

## Stage 1: inventory without assuming CSV inputs

Edit `inventory.json`. Add one entry per actual file to `files`. Start with the
following **shape**, substituting private facts and a real absolute path in the
analysis account only. This is not a claim about any actual input:

```json
{
  "files": [
    {
      "path": "/absolute/private/source-file",
      "role": "unknown",
      "format": "unknown",
      "table_organisation": "unknown",
      "private_table_details": "Record actual table/sheet names and counts here, or unknown.",
      "private_release_evidence": "Record release/version evidence and its private source here, or unknown.",
      "serialization": null
    }
  ],
  "missing_tokens": {"identifier": null, "age": null, "target": null},
  "indicator_blank_mapping": "unresolved"
}
```

Allowed `role`: `deaths`, `indicators`, `other`, `unknown`. Allowed `format`:
`delimited`, `xlsx`, `stata`, `spss`, `sas`, `parquet`, `json`, `other`, `unknown`.
Allowed `table_organisation`: `single_table`, `multiple_tables`, `multiple_sheets`,
`unknown`. Use private notes to describe unsupported formats precisely.

Check all file locations, accompanying release documentation and the native
application's metadata, where available. Record the actual number and names of
tables/sheets privately; do not assume a workbook has one sheet or that the
inputs correspond to exactly two files. Identify which tables supply the deaths
and indicator roles. If your native application/interface is unfamiliar, stop
and obtain its version-specific documentation privately; this tool does not
invent menu paths or readers. Do not export participant excerpts for help.

The `inventory` command records the actual number of listed inputs and checks
their leading bytes for gzip, ZIP, bzip2, xz and zstd containers. A signature is
an observation, not proof of the native file format. `no_recognized_container`
does not prove absence of compression. File extensions are not used as evidence.
`private_table_details` and `private_release_evidence` are never copied into
the candidate summary. Include necessary release-safe organisation/version facts
in an explicitly approved review statement.

## Stage 2: declared serialization

For a single delimited table, set `format` to `delimited` and enter known parsing
settings. This example declares a particular dialect; it is not an inferred
default for your files:

```json
"serialization": {
  "encoding": "utf-8",
  "delimiter": "comma",
  "quote": "double",
  "escape": "none",
  "doublequote": true,
  "header_row": 1
}
```

- Encodings: `utf-8`, `utf-8-sig`, `utf-16`, `cp1252`, `latin-1`.
- Delimiters: `comma`, `semicolon`, `tab`, `pipe`.
- Quote: `double`, `single`, `none`; escape: `none`, `backslash`.
- `doublequote` is a JSON boolean. `header_row` is a positive **CSV record
  number**, including any preamble records, not a physical line number when
  quoted fields span lines. Each later record must have the header's field count.

The Python inspector reads plain or gzip-compressed delimited text with those
settings. It does not sniff or convert encodings, guess separators, trim fields,
coerce identifiers to numbers, infer null tokens or normalize labels. Successful
parsing proves only that the parser accepted the declarations; a wrong encoding
or delimiter can still parse. Check the export documentation and schema results.
Keep `serialization: null` if you cannot establish the settings.

Other formats/containers remain `unsupported`. No reader for workbooks or native
statistical formats is bundled. Review their metadata privately using a known
local tool, record the unknowns, and plan a separately verified conversion. The
wizard cannot promise conversion commands before the native format is known.
If a computation is needed for preparation, use reviewed Python tooling; do not
substitute R or silently change the benchmark interface.

## Stage 3: documentary schema comparison

Inspect `observations.json` locally. The shipped `documented-schema.json`
contains names only, derived from JSON v1 F40 (33 deaths fields) and F41 (359
indicator-table fields, including 353 predictors and five COVID extras). The
source references are documented in `input-spec-review.md`. These names support
comparison with the documented v2 tables; they do not establish v2 equivalence.

For deaths, required fields are `IIntID`, `cause1_InterVA`, `Age_in_years`. For
indicators, required fields are `IIntID` and all 353 allowlisted indicators.
Other documented columns support an informative comparison but are not required
predictors. Extra headers are counted without emitting their names. Missing
required fields, blank/duplicate headers and malformed records remain findings.
No fuzzy field matching or automatic renaming occurs.

In `review.json`, put private v2 evidence under `v2_compatibility.private_evidence`.
Keep its `status` unresolved unless you have verified the actual release/schema.

## Stage 4: characteristics and meanings

All counts concern the inspected tables before linkage/eligibility filtering;
these are not benchmark inclusion/exclusion counts. Some diagnostics overlap.

- Identifier checks count blanks, leading zeros, digit strings larger than the
  exact binary64 integer range, surrounding whitespace and decimal/exponent
  spellings. They preserve strings exactly. They cannot recover precision or
  leading zeros lost before this inspection; verify native/export provenance.
- Duplicate groups count distinct repeated nonmissing keys. Duplicate rows
  count **all** rows in those groups. Conflicting-target keys have more than
  one exact target string, including blank-versus-nonblank differences. Neither
  duplicates nor conflicts are repaired.
- Linkage compares distinct exact strings, excluding blanks and declared
  missing identifiers. It requires exactly one inspected table per role with
  `IIntID`; multiple parts/sheets require an explicit preparation decision.
  `one_to_one` checks nonmissing key uniqueness, not completeness or eligibility.
- Indicator counts cover only present allowlisted fields: literal `y`, `n`, `-`,
  blank and unexpected. Missing columns are schema findings. No unexpected
  values or labels are listed. The `-` state stays separate from `n`.
- Age checks count blanks, declared missing tokens and nonfinite, negative,
  nonnumeric or fractional numbers. They do not confirm reference time or an
  upper bound. A positive integer sentinel can look like a valid year count
  until the user declares it missing. Adult eligibility is Ticket 02's work.
- Target checks count blanks and declared missing tokens, without enumerating
  labels. Undetermined meaning must come from your private evidence.

For each field in `missing_tokens`, `null` means **unknown**, `[]` means you
explicitly declare no special missing tokens, and a list of strings declares
exact tokens. Include `""` explicitly if blank is a declared missing token;
blanks are always counted separately. Do not copy the example tokens from tests
as actual-input conventions. `indicator_blank_mapping` is `unresolved`, `reject`
or `missing_inapplicable`; it records the preparation decision and does not
rewrite cells or merge the reported counts. Rerun `inspect` after any change.

Record evidence and separate release wording for `identifier_preservation`,
`age_at_death`, `missing_conventions`, `undetermined_assignment` in `review.json`.
The missing-conventions statement should specify exact approved age, identifier,
target and indicator blank/null handling. The undetermined statement should give
the precise documented label, or an explicit unresolved question. Automated
counts alone cannot establish these meanings.

## Stage 5: preparation decision

Record under `preparation` whether the sources already satisfy the two UTF-8 CSV
interface or need conversion, sheet selection, concatenation, field mapping,
decompression or another explicit step. Preserve identifiers losslessly, all
three indicator states and exact target labels. Document how preservation will
be checked before and after any conversion. Keep native paths and detailed
private evidence in `private_evidence` only.

Record unresolved questions explicitly, including missing v2 evidence, lossy
identifier history, unexpected codes, conflicts or uncertain age/target meanings.
The tool cannot override the accepted protocol or provide an unverified converter.
If prepared files are later inspected, keep the native inventory/evidence in the
original run directory and use a new evidence directory for those files. Refer
to both privately in the preparation decision.

## Stage 6: review and manual transfer

Every topic in `review.json` has:

```json
{
  "status": "unresolved",
  "private_evidence": "Private evidence reference and unresolved details; never copied.",
  "release_statement": "A separate, minimal statement safe for release, or empty.",
  "release_approved": false
}
```

Status choices are `unresolved`, `documentary_only`, `user_confirmed`.
`user_confirmed` requires a nonempty private evidence reference; the program
does not read that reference or establish its truth. A release statement is
copied only when `release_approved` is `true`. Leave unresolved topics unresolved,
even when releasing a statement describing the question.

The `release_sections` object separately selects `inventory`, `serialization`,
`schema`, `characteristics`. Each defaults to `false`. After local review, set
only the sections you intend to include to `true` and run `summary`. The summary
contains selected categorical facts/aggregates, approved statements, documentary
expectations and explicit blockers. Changed inventory requires reinspection.
Sources can change outside this tool: confirm they stayed unchanged during
inspection and review; start another run after any source change.

Open **only `candidate-summary.md`** for final release review. Its automatic
projection excludes private paths, arbitrary headers, identifiers, row excerpts,
observed target/code values, evidence references and error text. Your approved
free text is necessarily your responsibility: do not paste private reports,
contracts, logs or record values into it. Review aggregates, including small
counts, against your disclosure rules. No numerical disclosure threshold is
invented by this tool. Remove anything unsuitable before release.

When satisfied, manually transfer the approved document alone, optionally renamed
`reviewed-input-evidence.md`, into:

```text
docs/issues/interva5-replication/reviewed-input-evidence.md
```

Do not transfer `inventory.json`, `review.json`, either observations file,
`wizard.env`, source inputs, raw logs or the entire run directory. The wizard
does not copy, upload, commit or mark evidence approved. No predictions or fitted
models are produced. Tell the development account when the reviewed document is
available; link it from Ticket 01 then. Ticket 01 remains open until this handoff;
Ticket 02 remains blocked wherever required conventions/preparation are unresolved.
