# Issue tracker: Local Markdown

Specs and tickets live in Markdown files under `docs/issues/`. Publishing to the issue tracker means creating or updating a local file there; GitHub Issues is not this project's tracker.

## Conventions

- One feature per directory: `docs/issues/<feature-slug>/`.
- The feature spec is `docs/issues/<feature-slug>/spec.md`.
- Implementation tickets are separate files at `docs/issues/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` within the feature. Create tickets only when the task calls for them.
- Record triage state in a `Status:` line near the top, using [the configured role strings](triage-labels.md).
- Fetch a referenced spec or ticket by reading its file. Resolve a bare ticket number within the referenced feature; ask if multiple features make it ambiguous.
- Append discussion under `## Comments` when needed. Use relative Markdown links between repository documents.
- Publishing a spec or marking it `ready-for-agent` does not override an explicit instruction deferring implementation.

## Wayfinding

When using a wayfinding workflow, keep its map at `docs/issues/<effort>/map.md` and one child ticket per file in the effort's `issues/` directory. Record the ticket's kind in `Type:` and its dependencies in `Blocked by:` using links to local tickets.

Track execution separately from triage with `Progress: open`, `Progress: claimed` or `Progress: resolved`. Claim before work; resolve by appending an answer and updating the map with a short finding and ticket link. A ticket is unblocked when every listed dependency is resolved. Among open, unblocked, unclaimed tickets, choose the first by number.
