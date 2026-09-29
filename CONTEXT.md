# Verbal-autopsy classification

Vocabulary for the fresh design of a program that learns to reproduce InterVA5 first-cause assignments from verbal-autopsy indicators.

## Language

**Verbal-autopsy record**:
Information collected by verbal autopsy about a deceased person, including reported symptoms and circumstances preceding death.

**Verbal-autopsy indicator**:
A documented response or derived observation about a symptom, characteristic or circumstance that may inform cause-of-death estimation.

**Missing/inapplicable indicator response**:
The combined response state for missing or inapplicable information. It remains distinct from both an affirmative response and a negative response; its two meanings cannot be separated from the recorded state alone.

**Harmonisation**:
The mapping of responses from different questionnaires or coding schemes into a common set of documented indicators.

**Assigned cause of death**:
A cause attributed to a death by a classification method. An existing algorithm's assignment is an estimate, not an independent reference cause.
_Avoid_: Confirmed cause, ground truth

**InterVA5 first-cause label**:
The first cause recorded by InterVA5 for a verbal-autopsy record. It is the target that this project's classifier is intended to reproduce.

**Adult death**:
A death occurring at age 18 years or older. This defines the population in scope for the replication experiment.

**Undetermined assignment**:
An explicit InterVA5 outcome that does not assign a named cause. It is a target class for replication when documented as such, and is distinct from an absent target label.

**Replication model**:
A classifier trained to predict the recorded InterVA5 first-cause label from verbal-autopsy indicators.

**Replication agreement**:
The extent to which a replication model's predictions match recorded InterVA5 first-cause labels. Agreement measures reproduction of InterVA5 assignments, not accuracy against independently established causes of death.

**Benchmark population**:
The eligible labelled adult records whose InterVA5 target classes are retained for the experiment. Removing a cause class also removes its records from both training and evaluation, so reported agreement applies to this restricted population.

**Reference cause of death**:
A cause established through evidence independent of the classification method being evaluated and used as a comparison in validation. Its evidential basis determines its suitability as a reference.

**Invented teaching fixture**:
A fictional verbal-autopsy example created to illustrate or test software behaviour, without using participant records.
