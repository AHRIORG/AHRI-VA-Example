# Supplied input specifications

Reviewed 29 September 2026 for a fresh design. This review concerns documentation only; it establishes nothing about an actual participant file. Statements about historical algorithms and thresholds describe the supplied documents, not accepted requirements.

Sources: [JSON specification](/Users/kobush/AHRI-VA-Example/docs/data_specs/AHRI.VerbalAutopsy.Harmonisation.json) and [PDF specification](/Users/kobush/AHRI-VA-Example/docs/data_specs/VerbalAutopsy.Harmonisation_Data.pdf). PDF references below use printed pages; the corresponding physical PDF page is two pages later.

## Documented facts and implications

| Subject | Documentary evidence | Design implication |
| --- | --- | --- |
| Release | JSON `/study_desc/version_statement/version` identifies v1.0.0; its two `/data_files` names end in `.v1`. PDF pp4, 10 identify v2.0.0 and `.v2` files. | Authority and equivalence are unresolved. |
| Tables | JSON F40 and F41 and PDF pp4, 6, 10 describe a 33-variable deaths table and a 359-variable harmonised indicator table. The deaths table includes registered deaths; the detailed table covers completed verbal autopsies. | Completed-autopsy results do not automatically represent all registered deaths. |
| Indicator columns | JSON F41 contains `IIntID`, 353 `i…` fields and five COVID fields; PDF pp4, 64 says the COVID extras were not used in its cause estimation. | Available fields and method-supported fields must be distinguished. |
| Response codes | PDF p4 defines `y`, `n` and `-`, with `-` combining unknown and not applicable. Character-indicator category arrays in JSON are empty. | Unknown/inapplicable must not silently become negative. The lost distinction cannot be recovered from these codes alone. |
| Numeric exception | JSON V5271 and PDF p64 define `covid_test_r`: 1 positive, 2 negative, 3 unclear, 993 refused, 997 not applicable, 998 unknown, plus metadata `Sysmiss`. | A universal yes/no decoder would be incorrect; actual missing-value serialization is unspecified. |
| Age coverage | PDF pp4, 36–37 and JSON `i022a`–`i022n` describe adult, child and neonatal indicators, with overlapping groups; the deaths documentation includes probable stillbirths. | Population scope and age-boundary interpretation require decisions and further documentation. |
| Identity and provenance | JSON F40 V4882/F41 V4915 and PDF pp31–32, 36 document `IIntID` in both tables. `Questionnaire` is in the deaths table, with indicative historical periods. | No formal uniqueness, join-cardinality or duplicate-handling contract is supplied. Provenance may require a metadata join. |
| Previous estimates | JSON F40 V4897–V4914 and PDF pp4, 33–35 describe prior InterVA/InSilicoVA assignments, likelihoods/probabilities and intervals. | These are previous algorithm outputs, not documented independent reference diagnoses. The user subsequently chose the recorded first InterVA5 cause as the supervised target; the outputs are not prediction features. |
| Harmonisation | PDF pp4–5, 7–8 describes inputs prepared for InterVA5 and InSilicoVA, and lists separate correspondence tables and an ICD-10 mapping. | The attachments alone do not establish scientific compatibility with any chosen implementation or fully define the output cause list. |

## Unresolved documentary contract

- Actual serialization, delimiter, character encoding, null/blank spellings and column-order requirements are unspecified. JSON `missing_data` and `data_checks` are null.
- Several indicator labels are truncated. Empty questionnaire-detail fields do not repair the omissions.
- Questionnaire changes span four described periods, and the PDF warns that comparability can differ by cause. Comparable names do not establish comparable information across periods.
- The label “<1 month (28 days)” and overlapping neonatal and reproductive-age fields are insufficient to implement precise age rules.
- PDF p7 uses `VAInterview`; the dictionary uses `VAInterviewType`. Prior InterVA likelihood metadata also has an unexplained missing-code representation (`11` labelled `..`). Neither ambiguity should be silently decoded.
- The PDF's InSilicoVA reporting thresholds (40% for the leading cause and 20% for subsequent causes) are historical reporting conventions. They have not been adopted for this program.

Actual-input assumptions remain open until the user reviews them privately. Software tests with invented fixtures can establish intended behaviour, but cannot establish predictive validity on the study population.

## Selected replication target and supporting metadata

The user selected the first InterVA5 cause in the v2 deaths table as the machine-learning target. Its documented column is `cause1_InterVA`, a character field (JSON F40 V4897; PDF printed p33, physical p35). The PDF names the companion indicator table `AHRI.HDSS.VA-detailed-input-data-2000-2024.v2` (printed p10). The JSON still identifies the earlier release, so its agreement with selected PDF fields does not establish complete v2 equivalence.

Neither attachment supplies a complete category vocabulary, literal missing tokens or a precise undetermined-value contract for `cause1_InterVA`. The PDF's explicit InSilicoVA thresholds must not be applied to this InterVA target.

The deaths dictionary documents possible audit and validation attributes: `DoD_ym` (year/month of death), `Questionnaire`, `VAVisitDate`, `VAInterviewType`, `Age_in_years`, `Age_in_days` and `Sex` (printed pp31–32). Their existence in metadata does not guarantee actual completeness or suitability for grouping. No household, interviewer, respondent-identity or record-level geographic identifier is documented in these two tables. A validation split and its generalization claim remain design decisions.

`IIntID` is documented as numeric in both tables. The actual key parsing rules, uniqueness and join cardinality must be verified privately before combining indicators and target labels.

## Adults-only eligibility

The user limited the experiment to adults 18+. The indicators cannot implement that exact cutoff: `i022c` combines ages 15–49 and `i022l` combines females aged 12–19 (JSON F41 V4922/V4931; PDF printed pp36–37).

The deaths table's `Age_in_years` is labelled “Age in completed years Numeric,” with numeric type and zero displayed decimals (JSON F40 V4886; PDF printed p31). It is a candidate eligibility field, conditional on privately confirming its reference time is death and its missing-value conventions. The label alone does not establish the derivation, actual precision or valid sentinel handling. `Age_in_days` is explicitly described for deaths before age one and is not a substitute for adult eligibility (V4887, same page).

For later private validation: `DoD_ym` is documented as character width 7 but does not specify the exact date serialization. `Questionnaire` is numeric with documented categories 1–6 and 997 for not applicable. `IIntID` has zero displayed decimals in both dictionaries; this is not proof of lossless actual-file identifier parsing or uniqueness. These facts retain the JSON-v1/PDF-v2 qualification.

## Evaluation background

The [WHO 2022 instrument documentation](https://cdn.who.int/media/docs/default-source/classification/other-classifications/autopsy/2022-va-instrument/verbal-autopsy-standards_2022-who-verbal-autopsy-instrument_v1_final.pdf) distinguishes population mortality estimation from uncertain individual attribution. The [openVA methods paper](https://journal.r-project.org/articles/RJ-2023-020/openVA-RJ-R1.pdf) describes algorithms, symptom–cause information and individual/population outputs. Agreement with a previous algorithm must be distinguished from accuracy against an independent reference.

For the selected Python replication task, scikit-learn documents [classification metrics and dummy baselines](https://scikit-learn.org/stable/modules/model_evaluation.html) and [separating held-out evaluation from learned preprocessing and model selection](https://scikit-learn.org/stable/common_pitfalls.html). Overall accuracy measures the fraction of matching labels; macro F1 gives each evaluated class equal weight in the average. These are candidate evaluation measures, not an accepted ranking objective or performance threshold. No model artifacts or real data were inspected.
