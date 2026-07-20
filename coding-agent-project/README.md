# Mini AI Coding Agent

A small prototype that uses Anthropic's Claude API to generate code, validate
it automatically, and self-correct when validation fails. Built to explore
the core mechanics behind an "AI coding agent": a code generator paired with
a validation pipeline, with the model fixing its own mistakes based on real
tool output rather than a human relaying the error back manually.

## How it works

1. You describe a coding task in plain English.
2. Claude generates a solution file and a matching pytest test file, written
   against a fixed coding-standards prompt (PEP8, type hints, docstrings, no
   bare excepts, no emoji/non-ASCII characters).
3. The generated files are written to disk and run through automated
   validation:
   - A fast syntax check (Python's `ast` module) catches broken code and
     reports it as a short, targeted message instead of a long pytest
     collection-error traceback.
   - If the syntax is valid, pytest checks correctness and flake8 checks
     style.
4. If validation fails, the exact error output is fed back to Claude, which
   is asked to fix the code. This repeats for up to 4 iterations or until
   validation passes.

## Project structure

- `coding_agent.py` — the core pipeline: calls the Claude API, parses the
  reply into files, writes them, runs validation, and drives the
  generate-validate-correct loop. Runnable directly from the command line.
- `streamlit_app.py` — an optional browser front end for the same pipeline.
  Imports and reuses the functions in `coding_agent.py` rather than
  duplicating any logic; it only adds a UI on top (task input box, live
  per-iteration status, pass/fail summary, and the generated code in
  tabs).
- `requirements.txt` — Python dependencies (`anthropic`, `pytest`, `flake8`,
  `streamlit`).

## Setup

```
pip install -r requirements.txt
```

Set your Anthropic API key as an environment variable in the same terminal
session you'll run the agent from:

```
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running it

Command line, with the built-in default task (a palindrome checker):

```
python coding_agent.py
```

Command line, with your own task:

```
python coding_agent.py "Write a function that merges overlapping time intervals"
```

Browser UI:

```
streamlit run streamlit_app.py
```

This opens a page at `http://localhost:8501` with a text box for the task, a
"Run agent" button, and a live view of each iteration: a one-line pass/fail
summary, the generated code (collapsed by default), and the full pytest/
flake8 output (also collapsed by default, for anyone who wants the detail).

## What's actually been verified

This has been run live against several real tasks (a palindrome checker, a
prime-number checker, an email validator, tiered-volume-discount pricing,
and time-interval merging). In multiple runs the first attempt failed
validation — either a genuine bug or a style violation — and the second
attempt, informed by the validation output, passed cleanly. That
generate-fail-correct-pass cycle is the actual behaviour being demonstrated
here, not just a harness that happens to work when everything goes right on
the first try.

## Known limitations

- Generated code is not reviewed by a human before being written to disk or
  executed by pytest — for a task like this (a personal prototype run
  locally), that's an acceptable tradeoff, but it would not be safe to run
  unreviewed, unsandboxed LLM-generated code in a public-facing deployment.
- The file-parsing convention (`### FILE: name` markers in the model's
  reply) is a lightweight, regex-based alternative to Claude's native
  tool-use/function-calling API. Switching to tool use would be a more
  robust way to get structured output from the model.
- Only two files (a solution and its test file) are supported per task;
  there's no support for multi-file projects.

## Possible next steps

- Use Claude's tool-use API instead of regex-parsed file markers.
- Make the coding-standards prompt configurable per task instead of fixed.
- Add a retry budget/cost tracker so a run can't loop indefinitely on a
  stubborn task.
- Add static type checking (mypy) as a third validation layer alongside
  pytest and flake8.
