# Triage labels

The user selected the default triage vocabulary. In the local Markdown tracker, record the role in a `Status:` line rather than applying a remote label.

| Canonical role | Status value | Meaning |
| --- | --- | --- |
| needs-triage | needs-triage | Maintainer needs to evaluate the issue. |
| needs-info | needs-info | Waiting for information. |
| ready-for-agent | ready-for-agent | Fully specified for agent work, subject to explicit user constraints. |
| ready-for-human | ready-for-human | Requires human implementation. |
| wontfix | wontfix | Will not be actioned. |

Use these values whenever a skill refers to a triage label. `ready-for-agent` does not authorize implementation that the user has deferred or access to private data.
