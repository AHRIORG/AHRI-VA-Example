# Adult InterVA5 first-cause replication benchmark

Status: ready-for-agent

The user confirmed the command-level testing seam. Ticket 01 tooling was authorized on 29 September 2026, and the [approved evidence summary](reviewed-input-evidence.md) has been transferred. Later tickets remain deferred; the [handoff review](issues/01-private-input-evidence-wizard.md#handoff-review--29-september-2026) records the remaining missing-value decisions.

## Problem Statement

The researcher wants to determine whether simple supervised machine learning can reproduce recorded InterVA5 first-cause labels from harmonised verbal-autopsy indicators for adults in the documented 2000–2024 study period. The repository contains an accepted design and two accepted architectural decisions, but no Python program or test suite.

Existing algorithm assignments are estimates, not independent reference causes of death. The benchmark must report replication agreement and explain its population limits. Some cause classes may have too few eligible labelled adults to support the required held-out test set and three-fold training cross-validation. Pooling such classes or reporting results as representative of all adult causes would change the agreed experiment.

The researcher needs a reproducible, interpretable program developed using invented teaching fixtures, then executed privately by the user in the separate analysis account.

## Solution

Deliver a small Python command-line package with separate `validate` and `benchmark` commands, pinned dependencies, a configuration template, invented examples and a concise usage guide. The supported interchange contract is two UTF-8 CSV files containing harmonised indicators and the companion deaths table with targets and eligibility metadata.

Reproduce `cause1_InterVA` for eligible adults aged 18 or older using the 353 documented harmonised indicators. Before splitting, exclude every target class with fewer than five otherwise eligible labelled adults, including an explicit undetermined class if it falls below the same cutoff. Preserve exact retained labels and require at least two retained classes.

Compare regularised multinomial logistic regression, a random forest and a most-frequent-training-label baseline under the accepted evaluation protocol. Produce one concise Markdown report with agreement, uncommon-cause diagnostics, exclusions, retained population coverage and reproducibility details. Technical completion requires correct software behaviour, not a promised agreement score or real-data execution in this account.

## User Stories

1. As a researcher, I want to reproduce recorded InterVA5 first-cause labels, so that I can measure replication agreement with the existing assignments.
2. As a research reviewer, I want the objective distinguished from validation against reference causes of death, so that I can interpret the evidence correctly.
3. As an analyst, I want separate validation and benchmark commands, so that I can check inputs before fitting models.
4. As an analyst, I want a documented two-file UTF-8 CSV interface and configuration template, so that I can prepare and verify inputs privately.
5. As an analyst, I want unresolved input conventions identified explicitly, so that documentation is not mistaken for verification of actual files.
6. As an analyst, I want lossless linkage keys and unambiguous one-to-one matching, so that distinct records cannot be joined accidentally.
7. As an analyst, I want duplicate identifiers and conflicting targets to stop the run, so that ambiguous linkage cannot enter the experiment.
8. As a researcher, I want unmatched records excluded and counted, so that I can understand incomplete linkage.
9. As a researcher, I want eligibility based on completed age at death of at least 18 years, so that the benchmark describes adult deaths.
10. As an analyst, I want missing or invalid ages excluded and counted, so that uncertain adult eligibility remains visible.
11. As a researcher, I want explicit undetermined assignments treated as a target class, so that this recorded InterVA5 outcome can be replicated.
12. As a researcher, I want unusable or absent labels excluded separately from undetermined assignments, so that missing labels cannot become an invented cause class.
13. As a researcher, I want exact cause labels preserved, so that pooling or relabelling cannot change the replication question.
14. As a researcher, I want predictors restricted to the 353 documented harmonised indicators, so that the model stays within the agreed feature boundary.
15. As a research reviewer, I want targets, identifiers, metadata and prior algorithm outputs excluded from predictors, so that they cannot leak into predictions.
16. As a researcher, I want affirmative, negative and missing/inapplicable responses kept distinct, so that missing information is not treated as a negative response.
17. As an analyst, I want undeclared indicator values rejected and blank mappings made explicit, so that unexpected coding cannot silently alter the experiment.
18. As a researcher, I want target-class counts calculated after linkage and adult/label eligibility checks, so that rare-class decisions reflect eligible labelled adults.
19. As a researcher, I want every class with fewer than five eligible labelled adults excluded before splitting, so that the agreed feasibility rule is applied consistently.
20. As a researcher, I want all records of excluded classes removed from training and evaluation, so that every model uses the same benchmark population.
21. As a research reviewer, I want each excluded class, its count and the retained fraction of eligible labelled adults reported, so that I can assess the experiment's population coverage.
22. As an analyst, I want a clear failure when fewer than two classes remain, so that an unusable classification experiment is not reported as complete.
23. As a researcher, I want one fixed-seed stratified split with approximately 20% held out, so that final evaluation remains separate from model development.
24. As a researcher, I want explicit class-coverage checks for the holdout and every development fold, so that stratification is not assumed to guarantee feasibility.
25. As an analyst, I want coverage failures to stop the run without changing the seed or protocol, so that the intended design is not silently replaced.
26. As a researcher, I want every learner to use the same development folds and test records, so that model comparisons are consistent.
27. As a researcher, I want a most-frequent-training-label baseline, so that I can compare learners with a simple reference strategy.
28. As a researcher, I want logistic regression and random forests with the agreed limited tuning budget, so that the benchmark remains simple and reproducible.
29. As a researcher, I want original class frequencies retained without weighting or resampling, so that training follows the accepted design.
30. As a research reviewer, I want learned preprocessing, tuning and learner selection restricted to training data, so that held-out records cannot influence development.
31. As a researcher, I want deterministic tie-breaking, so that equivalent cross-validation scores produce a reproducible choice.
32. As a researcher, I want exact-match agreement as the primary measure and macro F1 as a diagnostic, so that the report answers the replication question while exposing uncommon-cause weaknesses.
33. As a researcher, I want the training-selected learner marked in the test comparison, so that test results do not become another selection stage.
34. As a research reviewer, I want per-cause test support and recall, with unsupported results marked not estimable, so that missing evidence is not presented as zero performance.
35. As a researcher, I want frequent cause confusions explained concisely when useful, so that I can understand errors without a large default matrix.
36. As an analyst, I want seed, split/fold sizes, selected settings and package versions recorded, so that I can reproduce the run.
37. As an analyst, I want failed fits and non-convergence surfaced as incomplete experiments, so that partial results cannot be mistaken for a completed benchmark.
38. As an analyst, I want diagnostics containing field names and aggregate counts without participant values, so that validation does not expose individual records.
39. As an analyst, I want the report without persisted individual predictions or fitted models, so that the experiment produces only its agreed output artifact.
40. As a developer, I want verification using invented teaching fixtures exclusively, so that development remains independent of participant records and real-data artifacts.
41. As a researcher, I want private execution and release review to remain under my control, so that only reviewed aggregates leave the analysis account.
42. As a research reviewer, I want weak agreement accepted as a possible valid finding and claims restricted to retained classes, so that technical completion is not confused with desired results or all-cause performance.

## Implementation Decisions

- **Authority and purpose:** implement ADR 0001's replication objective and ADR 0002's cause-class exclusion policy together with the accepted design interview. This is retrospective population research and research review, not implementation of the original InterVA5 inference algorithm.
- **Package responsibilities:** provide configuration/input validation, lossless linkage and benchmark-population construction, shared partitioning and model evaluation, and concise reporting. Internal module boundaries remain implementation choices. All computations run in Python using appropriate libraries with pinned dependencies.
- **Commands:** `validate` and `benchmark` share the input contract and eligibility rules. Validation checks input readiness without model fitting; benchmarking validates inputs before running the experiment. Supply invented examples, a configuration template and private-execution guidance.
- **Input contract:** accept two UTF-8 CSV files corresponding to the documented v2 deaths and harmonised-indicator tables. The target is `cause1_InterVA`, the linkage key is `IIntID`, and the eligibility field is `Age_in_years`. Actual v2 schemas, identifier representation, completed-age-at-death semantics, blank/missing conventions and the literal undetermined label remain privately verifiable facts. Documentary agreement with the older JSON release does not establish cross-version equivalence.
- **Integrity and linkage:** missing required columns, malformed records, duplicate identifiers and conflicting target records stop the run. Require unambiguous one-to-one linkage without lossy floating-point key conversion. Any normalisation must be explicit. Exclude and count unmatched records. Diagnostics use field names and aggregate counts without participant values or record excerpts.
- **Eligibility and labels:** after linkage, retain valid completed ages at death of at least 18 with usable targets. Exclude and count declared missing/invalid ages and missing/unusable targets. A documented explicit undetermined assignment is a class distinct from an absent target. Preserve exact labels without automatic merging.
- **Predictors:** use an explicit allowlist of the 353 documented harmonised indicators. Exclude five additional COVID fields, all existing algorithm outputs, identifiers, targets and metadata. Metadata can support linkage, eligibility or evaluation context without becoming a predictor.
- **Encoding:** retain `y`, `n` and `-` as distinct explicit categories. The `-` state combines missing/inapplicable information and cannot become a negative response. Reject undeclared values and accept blanks only via an explicitly reviewed mapping. Fit learned preprocessing within each training-only pipeline.
- **Class exclusion:** after joining and adult/target eligibility checks, count records per exact target class. Remove each class with fewer than five eligible labelled adults before splitting, including undetermined when applicable. Remove all affected records from training and evaluation. Do not pool, relabel or tune the cutoff using model performance.
- **Coverage accounting:** report each excluded class and its eligible count. Compute the retained fraction as eligible labelled adults in retained classes divided by otherwise eligible labelled adults before rare-class exclusion. Keep exclusion reasons understandable and sequential counts reconcilable without double-counting. An empty denominator is not estimable and cannot yield a feasible benchmark.
- **Holdout and folds:** require at least two retained classes. Generate one approximately 80/20 stratified development/test split with seed 42. Verify at least one test and three development examples per retained class. Generate three stratified development folds once; verify every retained class occurs in each training and validation portion. Coverage failures stop the run without retrying seeds or changing the protocol.
- **Candidates:** compare regularised multinomial logistic regression at `C = 0.1, 1, 10` and random forests with 200 trees and minimum leaf sizes of 1 or 5, alongside a most-frequent-training-label baseline. Retain original frequencies without class weighting or resampling. Use seed 42 for randomized steps.
- **Selection and isolation:** compare candidates on the same development folds and report all three models on the same final test records. Choose settings and the learner by mean cross-validation exact-match agreement using development records only. Ties favour logistic regression, stronger regularisation within logistic regression, or larger leaf size within random forests. Fit each learner at its chosen setting and the baseline on the development portion for final reporting. Test scores cannot change the chosen learner, settings or protocol.
- **Completion:** reject failed fits, non-convergence and infeasible coverage. A partial experiment must not be reported as successfully completed. No minimum agreement score is required.
- **Report:** produce one concise Markdown report stating replication agreement among eligible labelled adults in retained classes; inclusion/exclusion counts; excluded-class counts and retained fraction; three model rows with test agreement percentages and macro F1; the learner chosen by training-only cross-validation; per-cause test support and selected-learner recall percentages; useful frequent confusions; and seed, split/fold sizes, settings and package versions. Mark unsupported causes not estimable, not zero performance. Successful accepted partitions should provide test support for every retained class.
- **Development and execution:** develop with source, documentation and invented fixtures only. Only the user executes real-data commands in the separate analysis account; no agent runs there. Intermediate predictions remain in memory, with no individual-prediction or fitted-model exports. The report stays in the analysis account until the user releases reviewed aggregates. Instructions and Git ignores are not access controls.

## Testing Decisions

- **Confirmed seam:** exercise the public application command boundary for `validate` and `benchmark`. Supply temporary invented CSV inputs and explicit fixture configuration; observe exit outcomes, diagnostics and the report. Prefer in-process command invocation for coverage plus a small packaging smoke test. Avoid introducing a separate public testing interface for every internal module.
- **Good tests:** assert external behaviour and accepted protocol invariants, not private helper calls, object layouts, incidental report whitespace or high scores on toy records. Invented-fixture results establish software behaviour only.
- **Coverage and prior art:** exercise input/configuration validation, population construction, partitioning, preprocessing/model selection and reporting through this boundary. There is no existing implementation or test suite; the accepted synthetic-verification cases and command contract are the starting point. Tests must not load participant datasets, existing fitted models or real-data artifacts.
- **Eligibility and integrity:** test the exact age-18 boundary, declared missing/invalid ages and targets, explicit undetermined assignments, malformed records, missing columns, lossless keys including leading zeros and large digit strings, duplicates, conflicting targets and unmatched records. Check counts and diagnostics without individual values.
- **Encoding and feature exclusions:** cover all three indicator states, undeclared values, and blank responses with and without a reviewed mapping. Verify that targets, identifiers, metadata, prior algorithm outputs and COVID extras cannot become predictors. Perturbing excluded non-feature values that do not affect eligibility or linkage must not change results.
- **Rare-class boundaries:** test class counts of four and five after eligibility checks, including undetermined. Verify whole-class removal before splitting, retained labels, excluded-class counts and the retained fraction. Include a class whose raw count is at least five but eligible count is below five, no eligible adults, no retained classes and only one retained class.
- **Feasibility:** test valid coverage and failures where the five-record cutoff alone is insufficient, including inadequate test capacity and missing classes in development training/validation folds. Verify failures without changed seeds, cutoffs or partition design, and common partitions across models.
- **Isolation and selection:** use controlled invented cases to check deterministic reruns, the fixed tuning budget, training-derived baseline, tie preferences and training-only preprocessing/selection. Held-out feature perturbations must not influence tuning or selection. Fixture-only checks may verify these invariants without adding production prediction exports. Verify failed fits and non-convergence cannot produce successful-completion claims.
- **Reporting and artifacts:** check all model rows, the training-selected marker, metric semantics, per-cause support, exclusion accounting, retained fraction, restricted-population wording and reproducibility details. Check not-estimable handling for absent support while ensuring successful partitions do not silently omit retained causes. Confirm no prediction or fitted-model files are produced.
- **Acceptance:** invented-fixture tests pass, the agreed protocol is enforced, and a complete synthetic benchmark generates the interpretable report. Real-data feasibility and findings require private user execution and review and are outside software acceptance.

## Out of Scope

- Implementing the Python program during this specification task; implementation remains deferred.
- Reimplementing InterVA5 inference, invoking R, validating independent reference causes, clinical use or official death certification.
- Children, neonatal populations, future unlabelled deployment, alternative targets or secondary assigned causes.
- Additional predictors, COVID extras, class pooling, weighting, resampling, broad model searches or revised tuning budgets.
- Private-input verification in this account, participant records, real-data artifacts, agents in the analysis account or unreviewed aggregate releases.
- Guaranteed private-data feasibility, a performance threshold, reliable estimates from sparse retained classes or claims across excluded causes and all adult deaths.
- Persisted individual predictions or models, dashboards and a large default confusion matrix.

## Further Notes

- ADR 0002 defines the benchmark population for ADR 0001, so these decisions belong in one combined implementation spec.
- Authority: [ADR 0001](../../adr/0001-replicate-interva5-first-cause.md), [ADR 0002](../../adr/0002-exclude-infeasible-cause-classes.md), the [accepted design interview](../../design-interview.md), [domain glossary](../../../CONTEXT.md) and [input-specification review](../../input-spec-review.md). Final Q21 acceptance supersedes earlier wording that the numerical cutoff awaited confirmation.
- Five eligible examples is a feasibility cutoff, not a reliability guarantee; a retained class may have only one test example.
- The user confirmed the command seam as the testing boundary on 29 September 2026. Configuration and diagnostic edge handling make the accepted rules testable without resolving private-input assumptions.
- This issue is tracked locally in Markdown under `docs`, as requested. Its `ready-for-agent` status records specification readiness and does not override the instruction deferring implementation or the data-free development boundary.
