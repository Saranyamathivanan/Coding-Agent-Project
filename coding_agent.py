from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

MODEL = "claude-sonnet-4-5-20250929"
MAX_ITERATIONS = 4
WORKDIR = Path(__file__).parent / "agent_output"
CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "coding_agent_fixes"
DISTANCE_THRESHOLD = 0.6

CODING_STANDARDS = """\
You are a senior Python engineer generating production code for a coding agent project.
Follow these standards on every file you write:
- PEP8 style, 4-space indentation, max line length 100.
- Every public function has a docstring and full type hints.
- No bare except clauses.
- Do not use emoji or other non-ASCII decorative characters anywhere in the code or comments.
- Write comments and docstrings the way a thoughtful human engineer would: plain, concise
  language that explains *why* something is done when it isn't obvious, not a restatement of
  what the code already says line by line. Avoid stiff, repetitive, or overly formal phrasing
  that reads like it was generated rather than written by someone who knows the code.
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
    """Send a task to Claude and return the response."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=CODING_STANDARDS,
        messages=history + [{"role": "user", "content": task}],
    )
    return response.content[0].text


def parse_files(reply: str) -> dict[str, str]:
    """Extract generated files from the response."""
    parts = re.split(r"### FILE:\s*(\S+)\s*\n", reply)
    files: dict[str, str] = {}
    for name, code in zip(parts[1::2], parts[2::2]):
        code = re.sub(r"^```[a-zA-Z]*\n|```$", "", code.strip(), flags=re.MULTILINE)
        files[name.strip()] = code.strip()
    return files


def write_files(files: dict[str, str]) -> None:
    """Write generated files to the working directory."""
    WORKDIR.mkdir(exist_ok=True)
    for name, code in files.items():
        text = code if code.endswith("\n") else code + "\n"
        (WORKDIR / name).write_text(text, encoding="utf-8")


def check_syntax() -> tuple[bool, str]:
    """Check generated Python files for syntax errors."""
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
    """Run syntax, test, and style checks."""
    syntax_ok, syntax_message = check_syntax()
    if not syntax_ok:
        return False, f"--- syntax check ---\n{syntax_message}\n"

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


def get_collection():
    """Open the collection used to store resolved errors."""
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(COLLECTION_NAME)


def retrieve_similar_fix(error_log: str) -> str | None:
    """Return a relevant fix from an earlier validation failure."""
    collection = get_collection()
    if collection.count() == 0:
        return None

    results = collection.query(query_texts=[error_log], n_results=1)
    documents = results.get("documents") or []
    if not documents or not documents[0]:
        return None

    distance = results["distances"][0][0]
    if distance <= DISTANCE_THRESHOLD:
        return results["metadatas"][0][0]["fix"]
    return None


def remember_fix(error_log: str, fixed_files: dict[str, str]) -> None:
    """Store a resolved validation failure for later use."""
    collection = get_collection()
    fix_text = "\n\n".join(f"### {name}\n{code}" for name, code in fixed_files.items())
    entry_id = f"fix-{collection.count() + 1}"
    collection.add(documents=[error_log], metadatas=[{"fix": fix_text}], ids=[entry_id])


def run_agent(task: str) -> None:
    """Generate and validate code until it passes or reaches the limit."""
    history: list[dict] = []
    current_task = task
    last_failed_log: str | None = None

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
            if last_failed_log is not None:
                remember_fix(last_failed_log, files)
                print("Embedded this fix into the vector database for future retrieval.")
            return

        retrieved_fix = retrieve_similar_fix(log)
        if retrieved_fix:
            print("Retrieved a similar past fix from the vector database -- using it as a hint.")
            current_task = (
                "The previous solution failed validation. Fix the code so it passes. "
                f"Here is the validation output:\n\n{log}\n\n"
                "A similar error was fixed before. Here is that past working fix for "
                f"reference (adapt it to this task, do not copy it blindly):\n\n{retrieved_fix}"
            )
        else:
            current_task = (
                "The previous solution failed validation. Fix the code so it passes. "
                f"Here is the validation output:\n\n{log}"
            )
        last_failed_log = log

    print(f"\nDid not pass validation within {MAX_ITERATIONS} iterations.")


if __name__ == "__main__":
    default_task = (
        "Write a function `is_palindrome(s: str) -> bool` that returns True if a "
        "string is a palindrome, ignoring case, spaces, and punctuation."
    )
    task_arg = " ".join(sys.argv[1:]) or default_task
    run_agent(task_arg)