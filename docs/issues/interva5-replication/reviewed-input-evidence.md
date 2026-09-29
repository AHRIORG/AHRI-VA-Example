# Reviewed input-evidence summary

APPROVED FOR RELEASE.

## Documentary expectations

The accepted interface is two UTF-8 CSV inputs with IIntID, cause1_InterVA, Age_in_years and the 353 documented indicators. JSON v1 supplies the name comparison; the PDF describes v2. Matching older names does not establish v2 equivalence.

Automated observations use user-declared parsing and exact strings. They do not establish native identifier fidelity, age semantics or missing/undetermined meanings.

## v2_compatibility

Verification: user_confirmed. User-approved release statement:

> Both input tables correspond to the documented v2 release.

## identifier_preservation

Verification: user_confirmed. User-approved release statement:

> The CSV exports preserve the original IIntID values without changes.

## age_at_death

Verification: user_confirmed. User-approved release statement:

> Age_in_years gives age at death in completed years.

## missing_conventions

Verification: user_confirmed. User-approved release statement:

> Empty cells in Age_in_years and cause1_InterVA mean missing values.

## undetermined_assignment

Verification: user_confirmed. User-approved release statement:

> The exact InterVA5 first-cause label for an undetermined assignment is Undetermined

## preparation

Verification: user_confirmed. User-approved release statement:

> The two input files are UTF-8 CSV files. No further conversion is required.

## Selected automated observations

Listed input files: 2. Observed Python version: 3.12.1.

### Input 1

Inspection status: observed.

- role: deaths
- declared_format: delimited
- declared_organisation: single_table
- observed_container: no_recognized_container

Declared parsing settings (successful parsing alone does not verify correctness):
- encoding: utf-8
- delimiter: comma
- quote: double
- escape: none
- doublequote: True
- header_row: 1

- expected_fields: 33
- observed_fields: 33
- extra_field_count: 0
- predictors_present: 0
- missing_documented_fields: none
- missing_required_fields: none

- rows: 27726
- blank_identifiers: 0
- blank_targets: 0
- blank_ages: 0
- declared_missing_identifiers: 0
- declared_missing_targets: 0
- declared_missing_ages: 0
- leading_zero_identifiers: 0
- large_digit_identifiers: 0
- whitespace_identifiers: 0
- decimal_or_exponent_identifiers: 0
- non_completed_year_number_ages: 0
- duplicate_identifier_groups: 0
- duplicate_identifier_rows: 0
- conflicting_target_identifiers: 0
- indicator_y: unresolved / not available
- indicator_n: unresolved / not available
- indicator_missing_inapplicable: unresolved / not available
- indicator_blank: unresolved / not available
- indicator_unexpected: unresolved / not available

### Input 2

Inspection status: observed.

- role: indicators
- declared_format: delimited
- declared_organisation: single_table
- observed_container: no_recognized_container

Declared parsing settings (successful parsing alone does not verify correctness):
- encoding: utf-8
- delimiter: comma
- quote: double
- escape: none
- doublequote: True
- header_row: 1

- expected_fields: 359
- observed_fields: 359
- extra_field_count: 0
- predictors_present: 353
- missing_documented_fields: none
- missing_required_fields: none

- rows: 26168
- blank_identifiers: 0
- blank_targets: unresolved / not available
- blank_ages: unresolved / not available
- declared_missing_identifiers: 0
- declared_missing_targets: unresolved / not available
- declared_missing_ages: unresolved / not available
- leading_zero_identifiers: 0
- large_digit_identifiers: 0
- whitespace_identifiers: 0
- decimal_or_exponent_identifiers: 0
- non_completed_year_number_ages: unresolved / not available
- duplicate_identifier_groups: 0
- duplicate_identifier_rows: 0
- conflicting_target_identifiers: unresolved / not available
- indicator_y: 529409
- indicator_n: 1216046
- indicator_missing_inapplicable: 7491849
- indicator_blank: 0
- indicator_unexpected: 0

### Linkage

Distinct exact-string keys; blank and declared missing identifiers are excluded. Counts are provisional while identifier conventions remain unresolved.
- matched_unique_identifiers: 26168
- deaths_only_identifiers: 1558
- indicators_only_identifiers: 0
- one_to_one: True

## Handoff and unresolved questions

Ticket 02 remains blocked until the user reviews and manually transfers the approved evidence and resolves input-contract questions. No benchmark was fitted.

- Indicator blank handling remains unresolved.
