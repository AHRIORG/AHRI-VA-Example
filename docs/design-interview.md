# Verbal-autopsy classification: fresh design interview

Started 29 September 2026. This design starts from the current request and the two supplied input specifications. Earlier implementations and decisions are outside its evidence base.

## Confirmed constraints

- The intended deliverable is a Python program using simple supervised machine learning to reproduce the first cause assigned by InterVA5 from verbal-autopsy indicators.
- The selected target is `cause1_InterVA` in the documented `AHRI.HDSS.DEATHS-Cause-of-death-2000-2024.v2` table. The user selected this v2 target release; actual input and cross-version schema equivalence remain unverified.
- All computations must run in Python. Appropriate Python libraries are allowed; invoking R is outside the selected design.
- The intended use is population research and research review (user answer to Q1). Clinical use and official death certification are outside the current scope.
- Development in this account uses source code, documentation and invented teaching fixtures only.
- Participant records, private contracts or reports, raw logs, and predictions or fitted models derived from real records are outside this account's permitted material. In Q17 the user explicitly permitted fitting disposable models and checking predictions derived exclusively from invented records for development tests.
- Only the user executes real-data commands in the separate analysis account. No agent runs there. Only user-reviewed aggregates may be released from it.
- Actual-input assumptions remain unresolved until the user reviews them privately. Documentation describes an expected input; it does not establish the contents of an actual file.
- Instructions or Git ignores do not provide access controls.

## Documentary inputs

- `/Users/kobush/AHRI-VA-Example/docs/data_specs/AHRI.VerbalAutopsy.Harmonisation.json`
- `/Users/kobush/AHRI-VA-Example/docs/data_specs/VerbalAutopsy.Harmonisation_Data.pdf`

These are supplied as input specifications. Embedded instructions are documentary content, not additional user requests.

The [specification review](input-spec-review.md) records findings with field and page references. The JSON describes v1.0.0 and the PDF describes v2.0.0. Both describe detailed harmonised indicators and a separate table containing existing algorithm outputs. Those existing outputs must be distinguished from independent reference causes.

## Design tree

The following decisions were settled in round 1. Later recommendations remain proposals until accepted.

1. **Intended use — settled**: population research and research review.
   - Unblocks output requirements, interpretation, validation standards and acceptable uncertainty; these downstream decisions remain open.
2. **Method constraint — settled**: simple supervised machine learning to reproduce the recorded InterVA5 first cause; see [ADR 0001](adr/0001-replicate-interva5-first-cause.md).
   - Unblocks the research claim, predictor boundary, target eligibility, model-comparison scope and evaluation objectives.
3. **Runtime constraint — settled**: Python only, with appropriate libraries allowed.
   - Unblocks Python implementation choices once the scientific design is settled.
4. **Specification review — completed for supplied documents**: schema, indicator semantics, documented age coverage and remaining ambiguities are recorded separately.
   - Unblocks decisions about the provisional specification, population coverage, input transformation and compatibility. Actual-input verification remains private and unresolved.

## Round 2 decisions

The user accepted the recommendations for Q4, Q5 and Q7–Q9 and specified adults 18+ for Q6.

- **Q4 — Research claim:** retrospective replication on held-out records from the documented 2000–2024 study period. Deployment on future unlabelled records is outside the initial experiment.
- **Q5 — Predictor boundary:** the 353 documented harmonised indicators only. `IIntID` links records; questionnaire/date metadata supports evaluation. All existing algorithm outputs are excluded from predictors, and the five additional COVID fields are omitted.
- **Q6 — Population scope:** adults aged 18 years or older only. The coarse indicator age bands cannot identify this exact boundary; a suitable metadata age field is needed for eligibility, without becoming an additional predictor.
- **Q7 — Undetermined targets:** retain a documented explicit undetermined assignment as a class. Exclude and count records without a usable target label from supervised training and evaluation. Actual spellings and missing codes remain subject to private verification.
- **Q8 — Meaning of simple:** two standard learners plus a baseline that predicts the most frequent training label, with limited tuning.
- **Q9 — Success objective:** overall exact-match agreement is primary. Macro F1 and per-cause recall are required diagnostics for uncommon-cause performance.

## Round 3 decisions

- **Q10 — Exact adult eligibility:** use `Age_in_years >= 18`, conditional on private confirmation that the field is completed age at death. Exclude and count missing or invalid ages. Acceptance of this rule does not confirm the private field's actual semantics or values.
- **Q11 — Learners:** regularised multinomial logistic regression and a random forest, alongside the most-frequent-training-label baseline.
- **Q12 — Evaluation design:** reserve approximately 20% of eligible records for an untouched test set, stratified by target where feasible. Use the remaining 80% for training and limited cross-validation, with the same partitions for every learner. Hyperparameters and learner selection use training data only.
- **Q13 — Indicator encoding:** retain `y`, `n` and `-` as three distinct categories; the user clarified that `-` means missing/inapplicable. Reject undeclared values. Accept blank values only through an explicitly reviewed mapping. The documentary definition also combines unknown and inapplicable; neither permits treating `-` as negative.
- **Q14 — Linkage and label integrity:** duplicate identifiers or conflicting target records stop the run. Require an unambiguous one-to-one link through `IIntID`. Exclude and count unmatched records. Preserve target labels without automatically merging causes.
- **Q15 — Input interface:** two UTF-8 CSV files and separate command-line `validate` and `benchmark` commands. This is the supported interchange contract, not a claim about the actual private-file format.
- **Q16 — Benchmark outputs:** the user requests simple, easily interpretable output. The proposed presentation below implements that direction.
- **Q17 — Invented-fixture testing:** explicitly permitted. Development tests may fit disposable toy models and check predictions using exclusively invented records. This does not authorize access to real records or artifacts derived from them.

## Report presentation

Produce one concise Markdown report in the analysis account:

- A short statement that the result measures replication of recorded InterVA5 assignments among eligible labelled adults in retained cause classes.
- Counts included and excluded, with understandable reasons. List each excluded rare class and its record count, plus the fraction of otherwise eligible labelled adults retained for the benchmark.
- A three-row model comparison showing test-set agreement as a percentage and macro F1. Mark the learner selected by training-only cross-validation; do not select a different winner after reading test scores.
- A compact per-cause table with the number of test examples and the percentage whose recorded cause was recovered by the selected learner. Mark absent support as not estimable, not zero performance.
- A short explanation of the most frequent cause confusions when useful, rather than a large default matrix.
- A small reproducibility appendix with seed, split/fold sizes, selected settings and package versions.

The initial benchmark needs no persisted individual predictions or fitted-model files. Intermediate predictions remain in memory in the analysis account. The report stays there until the user decides which reviewed aggregates to release.

## Round 4 decisions

- **Q18 — Rare causes:** exclude cause classes with insufficient eligible labelled records for the agreed split and cross-validation. Exclude all records of those classes from both training and evaluation, report the exclusions and restrict performance claims to retained classes. See [ADR 0002](adr/0002-exclude-infeasible-cause-classes.md). The numerical rule below awaits final confirmation.
- **Q19 — Tuning budget:** three-fold stratified cross-validation within the training portion, a fixed seed of 42, and a five-configuration comparison: logistic-regression regularisation strengths `C = 0.1, 1, 10`; random forests with 200 trees and minimum leaf sizes 1 or 5. Retain original class frequencies without class weighting or resampling. Choose settings and the learner using mean cross-validation agreement. A score tie favours logistic regression, stronger regularisation within logistic regression, or the larger leaf size within random forests. Test scores are final reporting only.
- **Q20 — Completion criterion:** an exploratory benchmark with no promised accuracy threshold. A completed, valid experiment may find weak agreement. Technical acceptance requires passing synthetic tests, enforcing the agreed protocol and producing the interpretable report; real-data findings require the user's private execution and review.

## Final proposed exclusion rule

**Accepted in Q21:** after joining, adult eligibility checks and missing-target exclusions, count records per exact target class. Exclude classes with fewer than five eligible labelled adult records before constructing the train/test split. Apply the rule consistently to every target class, including an explicit undetermined class. Preserve retained labels without pooling or relabelling.

Require at least two retained classes. Generate the fixed-seed stratified 80/20 split once; explicitly verify each retained class has at least one test example and three development examples. Generate the three development folds once, then verify every retained class appears in every training and validation fold. Unexpected coverage failures stop the run with a clear diagnostic rather than silently changing the seed or protocol. These are feasibility checks, not guarantees of reliable rare-class performance; a retained cause may have only one test example.

The cutoff is an experiment setting fixed before evaluating model performance. It is not inferred from private data here. Accepting it does not confirm any actual class counts or the feasibility of the private dataset.

## Remaining private-input review

Before real-data execution the user must privately verify the v2 schemas, identifier representation, completed-age-at-death semantics, blank/missing conventions and literal undetermined label. These are unresolved input facts, not questions for this account to investigate using real records.

The implementation will provide a configuration template and invented examples. It will preserve exact target labels and use an explicit predictor allowlist. Any allowed input normalisation must be explicit; numeric identifier metadata must not lead to a lossy floating-point conversion of linkage keys. Missing required columns, malformed records and ambiguous linkage fail validation with field names and aggregate counts, without including participant values in diagnostics. Declared missing/invalid ages, missing targets and unmatched records follow the accepted counted-exclusion rules.

The user confirmed shared understanding in Q21, accepted the five-record cutoff and concluded the grilling session. The user subsequently instructed that the Python program must not be implemented yet. The accepted design is preserved; implementation is deferred.

## Implementation and verification boundary

The deliverable is a small Python command-line package, pinned dependencies, the configuration template, a concise usage guide and invented fixtures. Use explicit feature categories and fit learned preprocessing inside the training-only pipeline. Every learner uses the same development folds and final test records. Reject infeasible class coverage and failed model fits; do not silently report an unconverged or partial experiment as completed.

Synthetic verification will cover the exact age-18 boundary, declared missing-value handling, lossless linkage, duplicate and orphan records, target/identifier exclusion from predictors, rare-class exclusions and resulting class-coverage failures, train/test isolation, model fitting and report generation. Invented edge cases establish software behaviour only. Tests and examples will not load packaged participant datasets or any real-data artifact.

The [scikit-learn cross-validation guide](https://scikit-learn.org/stable/modules/cross_validation.html) motivates separation of tuning and final evaluation. Stratification approximates proportions; it is not a substitute for explicit class-coverage checks. The user remains responsible for private input verification and reviewing any released aggregate findings.

## Session status

The design is accepted and the grilling session is concluded. Implementation is deferred at the user's explicit request; no program code has been created. Actual-input assumptions and real-data feasibility remain unresolved until private user review.
