# Mini AI Coding Agent

A small prototype that uses Anthropic's Claude API to write code, test it,
and fix its own mistakes. I built it to understand how an "AI coding agent"
actually works: not just a chatbot writing code, but a generator paired with
real validation, where the model sees its own errors and gets to fix them.

## How it works

1. You describe a coding task.
2. Claude writes a solution file and a test file.
3. The files are checked for syntax errors, then run through pytest and
   flake8.
4. If something fails, the error is sent back to Claude to fix. This repeats
   up to 4 times.

The agent also remembers past mistakes. Each time a failure gets fixed, the
error and fix are saved in a small vector database (Chroma). Next time a
similar error comes up, the agent looks up the closest past fix and gives it
to Claude as a hint. That's the retrieval-augmented generation (RAG) part.

## Files

- `coding_agent.py` — the main pipeline. Run it from the command line.
- `streamlit_app.py` — a simple browser UI for the same pipeline.
- `requirements.txt` — dependencies: anthropic, pytest, flake8, streamlit,
  chromadb.

## Setup

```
pip install -r requirements.txt
```

Set your API key:

```
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run it

```
python coding_agent.py
python coding_agent.py "Write a function that merges overlapping time intervals"
streamlit run streamlit_app.py
```

The browser version opens at `http://localhost:8501`.

## Tested on

Palindrome checker, prime-number checker, email validator, tiered-discount
pricing, time-interval merging. Several of these failed on the first try and
passed after Claude saw the real error and fixed it.

## Known limits

- No human reviews the code before it runs — fine for local testing, not
  safe for a public deployment.
- Files are parsed with a simple `### FILE: name` marker, not Claude's
  native tool-use API.
- Only one solution file and one test file per task.
- The vector database needs a few runs before it has anything useful to
  retrieve.

## Next steps

- Switch to Claude's tool-use API.
- Make coding standards configurable per task.
- Add a cost/retry tracker.
- Add mypy as a third validation layer.
