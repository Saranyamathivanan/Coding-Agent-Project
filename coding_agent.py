"""
Mini AI Coding Agent -- Claude-powered code generator + validation loop.

Built as a small portfolio prototype exploring the core mechanics behind the
OLT "AI Coding Agent" project brief: an agent that generates code aligned with
a fixed set of standards, validates its own output automatically, and
self-corrects when validation fails.

Pipeline:
  1. Take a coding task description.
  2. Ask Claude to generate a solution + tests, following a fixed style guide
     (the "industry standards" the agent should align to).
  3. Write the code to disk and run automated validation:
       a. A fast syntax check (Python's own `ast` module) so that broken code
          is caught and reported cleanly, instead of surfacing as a long,
          noisy pytest collection-error traceback.
       b. If syntax is valid: pytest (correctness) and flake8 (style).
  4. If validation fails, feed the errors back to Claude and ask it to fix
     the code. Syntax errors get a short, targeted message; test/lint
     failures get the relevant tool output.
  5. Repeat until validation passes or a max number of iterations is reached.

Setup:
    pip install anthropic pytest flake8
    export ANTHROPIC_API_KEY=sk-ant-...

Run:
    python coding_agent.py
    python coding_agent.py "Write a function that merges two sorted lists"

Notes:
    `max_tokens` is set generously (4096) so that more complex tasks (e.g.
    multi-tier logic, Decimal-based money handling) have enough room to
    finish generating both files without truncating mid-response -- a
    truncated response looks like a syntax error (unterminated string,
    unclosed bracket) right near the end of the file, which is a different
    problem from the model actually writing invalid code.

    All file I/O explicitly uses UTF-8. Claude's replies can contain
    characters (emoji, smart quotes, etc.) that Windows' default locale
    encoding (cp1252) cannot handle, which otherwise raises a
    UnicodeEncodeError when writing generated files to disk.

    pytest and flake8 are both run with cwd=WORKDIR and target "." (rather
    than the full absolute path), and with encoding="utf-8" explicitly set
    on the subprocess call. Without this, on a project path containing
    non-ASCII characters (e.g. a OneDrive folder name with Korean
    characters), flake8's output embeds the full absolute path and can come
    back garbled depending on the system's default locale encoding. Running
    from inside WORKDIR keeps the reported paths short and clean
    (solution.py:14:1: ...) and avoids the encoding mismatch entirely.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

MODEL = "claude-sonnet-4-5-20250929"  # swap for whichever Claude model you have access to
MAX_ITERATIONS = 4
WORKDIR = Path(__file__).parent / "agent_output"

CODING_STANDARDS = """\
You are a senior Python engineer generating production code for a coding agent project.
Follow these standards on every file you write:
- PEP8 style, 4-space indentation, max line length 100.
- Every public function has a docstring and full type hints.
- No bare except clauses.
- Do not use emoji or other non-ASCII decorative characters anywhere in the code or comments.
- Include a companion pytest test file covering at least: a normal case, an edge case,
  and one invalid-input case.
- Output ONLY two files, using exactly this format so the harness can parse them:

  ### FILE: solution.py
  <code>

  ### FILE: test_solution.py
  <code>

Do not include any explanation outside of the two FILE blocks.
"""


def ask_claude(task: str, history: list[dict]) -> str:
    """Send the conversation so far to Claude and return its text reply."""
    import anthropic  # imported lazily so the parsing/validation logic can be
                       # unit-tested without the SDK or an API key present.

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=CODING_STANDARDS,
        messages=history + [{"role": "user", "content": task}],
    )
    return response.content[0].text


def parse_files(reply: str) -> dict[str, str]:
    """Pull out '### FILE: name' blocks from Claude's reply into {filename: code}."""
    parts = re.split(r"### FILE:\s*(\S+)\s*\n", reply)
    files: dict[str, str] = {}
    # parts[0] is any preamble text; after that it's [name, code, name, code, ...]
    for name, code in zip(parts[1::2], parts[2::2]):
        code = re.sub(r"^```[a-zA-Z]*\n|```$", "", code.strip(), flags=re.MULTILINE)
        files[name.strip()] = code.strip()
    return files


def write_files(files: dict[str, str]) -> None:
    """Write generated files to the working directory.

    Uses UTF-8 explicitly: Claude's replies can contain characters (emoji,
    smart quotes, etc.) that Windows' default locale encoding (cp1252)
    cannot encode, which would otherwise raise a UnicodeEncodeError here.
    """
    WORKDIR.mkdir(exist_ok=True)
    for name, code in files.items():
        text = code if code.endswith("\n") else code + "\n"
        (WORKDIR / name).write_text(text, encoding="utf-8")


def check_syntax() -> tuple[bool, str]:
    """Check that every .py file in WORKDIR is syntactically valid Python.

    This runs before pytest so that syntax errors are caught and reported as a
    short, targeted message, instead of surfacing through pytest's noisy
    collection-error traceback (which buries the actual problem under many
    lines of internal importlib/pytest frames and makes it harder for the
    model to self-correct reliably).

    Returns (True, "") if every file parses cleanly, or (False, message) with
    a short description of the first syntax error found.
    """
    for path in sorted(WORKDIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source, filename=str(path))
        except SyntaxError as e:
            snippet = e.text.strip() if e.text else ""
            message = f"SyntaxError in {path.name}, line {e.lineno}: {e.msg}\n    {snippet}"
            return False, message
    return True, ""


def run_validation() -> tuple[bool, str]:
    """Run syntax check, then pytest and flake8, against the generated code.

    Returns (passed, log). If a syntax error is found, pytest/flake8 are
    skipped entirely and a short, targeted error message is returned instead
    of the traceback that would otherwise result.
    """
    syntax_ok, syntax_message = check_syntax()
    if not syntax_ok:
        return False, f"--- syntax check ---\n{syntax_message}\n"

    # cwd=WORKDIR + target "." keeps reported paths short (solution.py:14:1)
    # instead of the full absolute path, and encoding="utf-8" avoids garbled
    # output on project paths containing non-ASCII characters.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "."],
        cwd=WORKDIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    lint = subprocess.run(
        [sys.executable, "-m", "flake8", "--max-line-length=100", "."],
        cwd=WORKDIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    passed = result.returncode == 0 and lint.returncode == 0
    log = (
        f"--- pytest ---\n{result.stdout}\n{result.stderr}\n"
        f"--- flake8 ---\n{lint.stdout}"
    )
    return passed, log


def run_agent(task: str) -> None:
    """Run the generate -> validate -> self-correct loop for a single task."""
    history: list[dict] = []
    current_task = task

    for i in range(1, MAX_ITERATIONS + 1):
        print(f"\n=== Iteration {i} ===")
        reply = ask_claude(current_task, history)
        history.append({"role": "user", "content": current_task})
        history.append({"role": "assistant", "content": reply})

        files = parse_files(reply)
        if not files:
            print("Could not parse any files from the model's reply. Stopping.")
            print(reply)
            return

        write_files(files)
        print(f"Wrote: {', '.join(files)}")

        passed, log = run_validation()
        print(log)

        if passed:
            print(f"\nValidation passed on iteration {i}.")
            return

        current_task = (
            "The previous solution failed validation. Fix the code so it passes. "
            f"Here is the validation output:\n\n{log}"
        )

    print(f"\nDid not pass validation within {MAX_ITERATIONS} iterations.")


if __name__ == "__main__":
    default_task = (
        "Write a function `is_palindrome(s: str) -> bool` that returns True if a "
        "string is a palindrome, ignoring case, spaces, and punctuation."
    )
    task_arg = " ".join(sys.argv[1:]) or default_task
    run_agent(task_arg)
