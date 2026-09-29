---
status: accepted
---

# Exclude cause classes with insufficient examples for evaluation

The benchmark requires a held-out test set and three-fold training cross-validation. The user chose to exclude a cause class when it has too few eligible labelled adults to support that design, rather than stopping the entire experiment or combining causes. In Q21 the user accepted a cutoff of five eligible labelled adults per class, applied before splitting.

Exclusion removes all records of the affected class from training and evaluation. The report must show excluded classes, their record counts and the fraction of otherwise eligible labelled adults retained. Reported performance describes the retained classes only; it cannot establish performance across all adult causes of death.
