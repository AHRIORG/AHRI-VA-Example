---
status: accepted
---

# Learn to reproduce the recorded InterVA5 first cause

The research question is whether a simple machine-learning approach can reproduce InterVA5's first-cause assignments from verbal-autopsy indicators. The user selected `cause1_InterVA` in `AHRI.HDSS.DEATHS-Cause-of-death-2000-2024.v2` as the supervised learning target, fixing the objective as replication agreement rather than independent cause-of-death validation.

This target determines the meaning of training labels and evaluation results. Strong agreement would support reproduction of the recorded InterVA5 assignments; it would not establish accuracy against independently determined causes of death. The project is not an implementation of the original InterVA5 inference algorithm. The [design](../design-interview.md) specifies the adult population and evaluation protocol; actual target-value conventions remain subject to private user verification.
