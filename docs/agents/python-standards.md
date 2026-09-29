# Python Coding Standards for Code Review

A condensed review standard for an automated reviewer, distilled from
[PEP 8](https://peps.python.org/pep-0008/) (public domain) and the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
(CC BY 3.0). Wording is paraphrased; consult the originals for full rationale.

---

## 1. How to Use This Document

**Role split.** Formatters and linters handle mechanical style. The reviewer
handles judgment: readability, naming quality, design, error handling,
documentation accuracy, and correctness risks.

**Do not comment on anything an automated tool already enforces** (formatting,
line wrapping, import order, whitespace, quote style) provided the project runs
one of: Black/Pyink or Ruff format, Ruff/Flake8/Pylint, mypy/pyright/pytype.
If the project has no such tooling, apply Section 3 too, but at Low severity.

**Precedence when rules conflict:**

1. Project-specific configuration (`pyproject.toml`, `ruff.toml`, `.pylintrc`,
   `setup.cfg`) and any project style doc.
2. Consistency with the surrounding file or module. Both source guides rank
   local consistency above their own rules.
3. This document. Where PEP 8 and Google differ, the choice is stated in the
   "Resolved conflicts" table (Section 9).

**Do not flag** code that merely predates a guideline and is not otherwise being
modified. Never demand a change that would break backwards compatibility solely
for style.

---

## 2. Severity Levels

| Level | Meaning | Examples |
|-------|---------|----------|
| **High** | Likely bug or maintenance hazard. Should block merge. | Mutable default argument, bare `except:`, `assert` used for validation, leaked resource, `is` comparison against literals |
| **Medium** | Real readability or design cost. Should be fixed. | Vague names, missing docstring on public API, overly broad `try`, function doing too much, mutable global state |
| **Low** | Style deviation with minor cost. Fix if convenient. | Comment phrasing, minor naming inconsistency, unnecessary parentheses |
| **Nit** | Optional preference. Prefix with "Nit:". | Ordering of equivalent options, subjective wording |

---

## 3. Layout and Formatting (Low, unless a tool is absent)

- 4 spaces per indent level. Never tabs (except to match existing tab-indented code).
- Line length: follow the project setting. Defaults are 79 (PEP 8) or 80
  (Google); up to 99 is acceptable if the team has agreed. Comments and
  docstring text wrap around 72 in PEP 8 terms.
- Prefer implicit line joining inside brackets over backslash continuation. The
  only routine backslash use is inside string literals.
- Two blank lines between top-level definitions; one between methods. No blank
  line directly after a `def` line.
- No trailing whitespace. No spaces just inside brackets, before commas or
  colons, or before the opening bracket of a call or index.
- Single space around assignment, comparison, and boolean operators. No spaces
  around `=` for keyword arguments or unannotated defaults; spaces around `=`
  when the parameter has an annotation.
- Do not vertically align tokens across lines (`=`, `:`, `#`).
- One statement per line. No semicolons. A one-line `if x: y()` is tolerable
  only with no `else`; never for `try/except`.
- Trailing commas: use when the closing bracket is on its own line (helps diffs);
  required for one-element tuples.
- Break long expressions at the highest syntactic level. When breaking around
  binary operators, breaking before the operator is preferred for new code.
- Parentheses: use sparingly. Not needed around `if` conditions or `return`
  values unless continuing a line or forming a tuple.
- Strings: pick one quote style per file and stay consistent; use the other
  quote to avoid escaping. Triple-quoted strings and docstrings use `"""`.

---

## 4. Imports

- `import` statements at top of file, after the module docstring and before
  module-level code.
- One import per line. Exception: multiple names from `typing` or
  `collections.abc` on one line.
- Group in this order, blank line between groups, sorted alphabetically within
  each: `__future__`, standard library, third-party, first-party/local.
- **Never** use wildcard imports (`from x import *`), except deliberately
  re-exporting an internal interface. *(Medium)*
- Import modules and packages, not individual classes or functions (Google).
  Exempt: `typing`, `collections.abc`, `typing_extensions`. PEP 8 permits
  importing a class from a module; treat this as acceptable when the project
  already does so.
- Use `import x as y` only for standard abbreviations (`np`, `pd`) or to resolve
  a name collision or an unwieldy name.
- Prefer absolute imports over relative imports. Explicit relative imports are
  acceptable in complex package layouts if the project already uses them.
- Import only what is used; flag unused imports.
- Module dunders (`__all__`, `__version__`) go after the docstring and before
  imports (except `__future__` imports, which come first).

---

## 5. Naming

| Kind | Convention |
|------|-----------|
| Packages, modules | `lower_with_under` (no dashes; underscores in packages discouraged) |
| Classes, exceptions, type aliases | `CapWords`; acronyms fully capitalized (`HTTPServerError`) |
| Exceptions | Suffix `Error` when the exception is an error |
| Functions, methods, variables, parameters | `lower_with_under` |
| Constants | `UPPER_WITH_UNDER` |
| Internal names | Single leading underscore |
| Type variables | Short `CapWords`; `_co` / `_contra` suffixes for variance |

Review points:

- Names must be **descriptive**; descriptiveness should scale with scope. *(Medium)*
- Avoid abbreviations that are ambiguous or unfamiliar, and avoid deleting
  letters from within words.
- Avoid names that redundantly encode the type (`id_to_name_dict`).
- Single-letter names only for short-lived counters (`i`, `j`), `e` for
  exceptions, `f` for file handles, and established mathematical notation
  (with a comment citing the source).
- Never use `l`, `O`, or `I` as single-character names.
- First argument: `self` for instance methods, `cls` for class methods. Append a
  trailing underscore to avoid keyword clashes (`class_`).
- Do not invent `__dunder__` names.
- Prefer a single leading underscore over double (name mangling), which hurts
  readability and testability. Use double only to avoid subclass clashes.
- Files must end in `.py` and must not contain dashes.
- Test methods follow `test_<unit>_<state>`.

---

## 6. Language Rules

### 6.1 Errors and Exceptions

- **High:** No bare `except:`. Do not catch `Exception` unless re-raising or at a
  deliberate isolation point (e.g. protecting a worker thread's outer loop),
  where the error is logged.
- Catch the most specific exception possible.
- Keep `try` bodies minimal so unrelated errors are not masked; use `else` for
  code that should run only on success.
- Use `finally` or context managers for cleanup.
- **High:** Do not use `assert` for validation or control flow. Asserts can be
  stripped. Raise `ValueError` (or a suitable built-in) for bad arguments.
  `assert` is fine in tests and for checking genuine invariants.
- Custom exceptions inherit from `Exception` (or a more specific subclass),
  never directly from `BaseException`. Names end in `Error` and avoid
  repetition (`foo.FooError`).
- Use `raise X from Y` to chain deliberately; use `from None` only when
  suppressing context, and carry over relevant detail.
- Error messages must accurately describe the actual condition, clearly mark
  interpolated values (e.g. `f'{value=}'`), and be easy to grep.
- Prefer built-in exception classes and the OS-error subclasses over inspecting
  `errno`.

### 6.2 Resources

- **High:** Use `with` for files, sockets, connections, locks, and other
  closeable resources. Do not rely on destructors or garbage collection.
  Use `contextlib.closing` for objects lacking context-manager support.
- Context managers that do more than acquire/release should be invoked through
  a clearly named function or method.

### 6.3 Functions and Arguments

- **High:** No mutable default arguments (`[]`, `{}`, `set()`, or calls like
  `time.time()`). Use `None` and create inside the function.
- Prefer small, focused functions. Around 40 lines is a prompt to consider
  splitting, not a hard limit.
- Return consistently: if any path returns a value, every path must, using an
  explicit `return None` where appropriate.
- Prefer `def` over assigning a lambda to a name. Lambdas are acceptable inline
  when short (roughly under 60-80 characters); prefer `operator` module
  functions over trivial lambdas.
- Avoid `staticmethod`; write a module-level function. Use `classmethod` only
  for named constructors or class-level state.
- Decorators: use only with clear benefit, avoid external dependencies at
  decoration time, and unit-test them.

### 6.4 Truthiness and Comparison

- Compare to `None` with `is` / `is not`, never `==`. *(Medium)*
- Use implicit falsiness for sequences: `if not items:`, not `if len(items) == 0:`.
- Do not compare booleans with `== True` / `== False`.
- Beware `if x:` when `x` may legitimately be `0`, `''`, or an empty container
  and you actually mean `is not None`.
- Write `is not`, not `not ... is`.
- Use `isinstance()` rather than comparing `type()` values.
- Use `startswith()` / `endswith()` instead of slicing.
- Do not use `return`, `break`, or `continue` inside `finally` where it would
  swallow an in-flight exception.
- When defining ordering, implement all six rich comparisons or use
  `functools.total_ordering`.

### 6.5 Comprehensions, Iteration, and Expressions

- Comprehensions are fine when simple. **Not** more than one `for` clause or
  filter expression; use a loop instead. Optimize for readability.
- Iterate directly over containers (`for k in d`, `for line in f`) rather than
  `.keys()` or `.readlines()`. Do not mutate a container while iterating.
- Conditional expressions (`a if c else b`) only when each part fits on one
  line; otherwise use `if`.
- Do not build strings with `+=` in loops; collect in a list and `''.join`, or
  use `io.StringIO`.
- Use f-strings, `%`, or `.format()` for formatting rather than `+` chains.

### 6.6 State, Scope, and Structure

- **Medium:** Avoid mutable global state. If unavoidable, make it internal
  (leading underscore), expose through functions, and explain why in a comment.
  Module-level constants are fine.
- Nested functions/classes only when closing over a local value; do not nest
  merely to hide something (prefix with `_` at module level instead).
- Avoid "power features": custom metaclasses, bytecode/import hacks, dynamic
  inheritance, gratuitous reflection, custom `__del__`. Standard library
  users of these (`dataclasses`, `enum`, `abc`) are fine.
- Properties: only for cheap, unsurprising logic. Do not wrap a plain
  get/set of an attribute in a property (just expose the attribute). Do not
  use properties for expensive work or logic subclasses may need to override.
- Getters/setters are appropriate when the operation is non-trivial or costly.
- Decide deliberately whether each attribute is public, internal, or part of a
  subclass API. When in doubt, make it non-public.
- Declare the public API with `__all__`; prefix internals with `_`.
- Executable modules: put logic in `main()` and guard with
  `if __name__ == '__main__':`. No side-effecting work at import time.

### 6.7 Threading

- Do not rely on atomicity of built-in operations.
- Prefer `queue.Queue` for inter-thread communication; otherwise use
  `threading` primitives, preferring `Condition` over raw locks.

### 6.8 Logging

- Pass a string literal with `%s`-style placeholders and arguments to logging
  calls, not an f-string. This avoids rendering unneeded messages and keeps the
  template queryable. *(Medium)*

### 6.9 Portability

- Do not depend on CPython-specific optimizations (e.g. in-place string
  concatenation speed).
- Use `from __future__` imports where they enable modern behavior; do not
  remove them until you are sure the runtime no longer needs them.

---

## 7. Type Annotations

- Annotate **all public APIs**. Elsewhere, annotate code that is complex,
  bug-prone, or stable. Annotating every function is not required.
- Do not annotate `self`/`cls` (use `Self` if needed) or `__init__`'s `-> None`.
- Use `X | None` (Python 3.10+) or `Optional[X]`. **Never** implicit optional
  (`a: str = None`). *(Medium)*
- Use built-in generics (`list[int]`, `tuple[int, ...]`) rather than
  `typing.List` / `typing.Tuple` in modern code.
- Prefer abstract parameter types (`Sequence`, `Mapping`) over concrete ones.
- Give generics explicit type parameters; bare `Sequence` silently means
  `Sequence[Any]`. Use a `TypeVar` where `Any` would lose information.
- Do not use `typing.Text`; use `str` (or `bytes` for binary data).
- Import symbols from `typing` and `collections.abc` directly.
- Name `TypeVar`s descriptively, except unconstrained internal ones (`_T`).
- Type aliases: `CapWords`, annotated as `TypeAlias`, `_Private` if module-local.
- Forward references: `from __future__ import annotations` or quoted names.
- Do not add new `# type: <T>` comments; use annotations. Keep `# type: ignore`
  narrow and justified.
- Conditional (`TYPE_CHECKING`) imports and `Any` aliases for circular imports
  are last resorts; circular typing dependencies are a design smell.
- Variable annotations: one space after the colon, none before; spaces around
  `=` when assigned.

---

## 8. Comments and Documentation

### 8.1 Comments

- **A comment that contradicts the code is worse than none.** Flag stale
  comments. *(Medium)*
- Comment the *why* and the non-obvious, never a line-by-line description of
  what the code does.
- Comments should be clear sentences with sensible capitalization and
  punctuation, in English unless the codebase is guaranteed local.
- Block comments align with the code they describe; inline comments are
  separated from code by at least two spaces, start with `# `, and are used
  sparingly.
- `TODO` comments: `# TODO: <link to issue> - <explanation>`. Avoid pointing at
  a person or team as the only context. Give a specific date or event if the
  work is time-bound.
- Keep `# pylint: disable=` (and similar) targeted, with a reason when not
  obvious.

### 8.2 Docstrings

- Use `"""` triple double quotes. First line is a one-line summary ending in
  punctuation, then a blank line, then detail. Closing quotes on their own line
  for multi-line docstrings.
- **Required** for: public modules, classes, and functions/methods; and any
  function that is non-trivial or has non-obvious logic. Private helpers may
  use a comment instead. *(Medium when missing on public API)*
- A function docstring should give enough information to call the function
  correctly without reading its body. Describe behavior and contract, not
  implementation, except where the implementation matters to callers (e.g.
  mutates an argument).
- Use consistent section headings (`Args:`, `Returns:` / `Yields:`, `Raises:`)
  in the project's chosen docstring style (Google style by default).
  - `Args:` lists every parameter; include the type only if not annotated.
  - `Returns:` describes semantics beyond the annotation; describe a tuple
    return as a tuple, not as multiple named returns.
  - `Raises:` covers exceptions that are part of the interface. Do **not**
    document exceptions raised for API misuse.
  - Generators use `Yields:`.
- Classes: summary describing what an instance *represents*; document public
  attributes in an `Attributes:` section. Exception docstrings say what the
  exception means, not where it is raised.
- `@property` docstrings describe the value (`"""The Bigtable path."""`), not
  "Returns ...".
- Methods overriding a base method with `@override` need no docstring unless
  they change the contract.
- Docstrings for decorated callables describe post-decoration behavior.
- Do not write docstrings that only restate the name (`"""Tests for foo."""`).
- **Flag docstrings that no longer match the signature or behavior.** *(Medium)*
- Choose either descriptive ("Fetches...") or imperative ("Fetch...") mood
  and keep it consistent within a file.

---

## 9. Resolved Conflicts Between the Two Sources

| Topic | PEP 8 | Google | Reviewer applies |
|-------|-------|--------|------------------|
| Line length | 79 (72 docs); up to 99 with team agreement | 80 | Project setting; else 88-99 is fine, do not flag if a formatter enforces it |
| Import a class directly | Allowed | Import modules only | Follow project convention; otherwise prefer modules, flag only on collisions or confusion |
| Relative imports | Explicit relative OK | Not allowed in new code | Prefer absolute; do not flag explicit relative imports already in use |
| Quote style | No preference | Consistent per file | Consistency |
| Backslash continuation | Sometimes OK (`with`, `assert`) | Avoid | Avoid; parentheses work in modern Python |
| Lambda | Do not assign to a name | Fine for one-liners | Do not bind to a name; inline is fine |
| Docstring format | PEP 257 | Google sections | PEP 257 + Google sections |
| Annotations | Follow PEP 484 | Strongly encouraged for public APIs | Require on public APIs |

---

## 10. Reviewer Behavior

1. **Scope:** Review changed lines and their immediate context only. Do not
   audit unrelated legacy code.
2. **Prioritize:** Report High issues first. Cap Low/Nit comments; if there are
   many of the same kind, mention the pattern once.
3. **Be specific:** Cite the file and line, state the problem, state the
   consequence in one sentence, and propose a concrete fix or snippet.
4. **Justify with a rule:** Reference the relevant section of this document
   (e.g. "§6.3 mutable default") rather than saying "not Pythonic."
5. **Do not restate what tools catch.** Skip formatting, import sorting, and
   anything the CI linter already fails on.
6. **Respect consistency:** If the file uses a different but internally
   consistent style, do not flag it.
7. **Distinguish rules from taste:** Mark preferences as Nit and never block on
   them.
8. **Acknowledge uncertainty:** If a finding depends on context you cannot see
   (e.g. whether a global is intentional), ask instead of asserting.

### Suggested output format

```
[SEVERITY] path/to/file.py:LINE - Short title (§section)
Problem: what is wrong.
Why it matters: one-sentence consequence.
Suggestion: concrete fix or code snippet.
```

End with a brief summary: counts by severity and an overall recommendation
(approve / approve with comments / request changes).

---

## 11. Suggested Tooling (for the project, not the reviewer)

| Purpose | Tools |
|---------|-------|
| Formatting | Black, Pyink, or `ruff format` |
| Linting | Ruff (pycodestyle, pyflakes, bugbear, isort, bandit rules), Pylint, Flake8 |
| Type checking | mypy, pyright, or pytype |
| Docstring style | `pydocstyle` or Ruff `D` rules |

---

## Sources

- PEP 8, "Style Guide for Python Code": <https://peps.python.org/pep-0008/>
- PEP 257, "Docstring Conventions": <https://peps.python.org/pep-0257/>
- PEP 484, "Type Hints": <https://peps.python.org/pep-0484/>
- Google Python Style Guide: <https://google.github.io/styleguide/pyguide.html>
  (licensed CC BY 3.0; this document is a paraphrased, condensed adaptation)
