"""
Streamlit front end for the mini AI coding agent.

This is a thin UI layer only -- it imports and reuses the exact same
generate / validate / self-correct logic from coding_agent.py rather than
duplicating it, so the behaviour you already tested from the command line
is exactly what runs here.

Design: keep the per-iteration view compact. Each iteration shows a single
one-line pass/fail summary; the generated code and the full pytest/flake8
log are both tucked behind "View..." expanders for anyone who wants detail.
Once an iteration is superseded by the next one, it collapses automatically
so only the current/final iteration stays open.

Setup (in the same project folder as coding_agent.py):
    pip install -r requirements.txt

Run:
    streamlit run streamlit_app.py
    (or, if "streamlit" isn't on your PATH: python -m streamlit run streamlit_app.py)

This opens a browser tab at http://localhost:8501. Your ANTHROPIC_API_KEY
needs to be set in the same terminal session before you run this command,
same as with coding_agent.py.
"""

from __future__ import annotations

import re

import streamlit as st

from coding_agent import (
    MAX_ITERATIONS,
    ask_claude,
    parse_files,
    run_validation,
    write_files,
)

st.set_page_config(page_title="Mini AI Coding Agent", layout="wide")
st.title("Mini AI Coding Agent")
st.caption(
    "Generates a solution + tests with Claude, validates with a syntax check, "
    "pytest, and flake8, and self-corrects on failure."
)


def summarize_log(log: str) -> dict:
    """Turn the raw validation log into short, display-friendly numbers."""
    if log.startswith("--- syntax check ---"):
        return {"syntax_error": log.replace("--- syntax check ---", "", 1).strip()}

    pytest_part, _, flake8_part = log.partition("--- flake8 ---")
    pytest_section = pytest_part.replace("--- pytest ---", "", 1).strip()
    flake8_section = flake8_part.strip()

    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", pytest_section)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", pytest_section)) else 0
    test_errors = int(m.group(1)) if (m := re.search(r"(\d+) error", pytest_section)) else 0
    lint_issues = len([ln for ln in flake8_section.splitlines() if ln.strip()])

    return {
        "syntax_error": None,
        "passed": passed,
        "failed": failed + test_errors,
        "lint_issues": lint_issues,
    }


def render_summary_line(log: str) -> None:
    """One compact line: pass/fail/style counts, instead of a metrics block."""
    summary = summarize_log(log)
    if summary["syntax_error"] is not None:
        st.error("Syntax error — the generated code could not be parsed.")
        return
    st.write(
        f"✅ {summary['passed']} passed &nbsp;·&nbsp; "
        f"❌ {summary['failed']} failed &nbsp;·&nbsp; "
        f"⚠️ {summary['lint_issues']} style issues",
        unsafe_allow_html=True,
    )


def render_files(files: dict[str, str]) -> None:
    """Show generated files as tabs."""
    tabs = st.tabs(list(files.keys()))
    for tab, code in zip(tabs, files.values()):
        with tab:
            st.code(code, language="python")


task = st.text_area(
    "Describe the coding task",
    value="",
    placeholder="Enter the coding task here...",
    height=100,
)
run_clicked = st.button("Run agent", type="primary")

if run_clicked:
    if not task.strip():
        st.warning("Enter a task first.")
        st.stop()

    history: list[dict] = []
    current_task = task
    passed_on: int | None = None

    for i in range(1, MAX_ITERATIONS + 1):
        with st.status(f"Iteration {i}", expanded=True) as status:
            try:
                reply = ask_claude(current_task, history)
            except Exception as e:  # noqa: BLE001 -- surface any API error to the UI
                status.update(label=f"Iteration {i} — API error", state="error", expanded=True)
                st.error(str(e))
                st.stop()

            history.append({"role": "user", "content": current_task})
            history.append({"role": "assistant", "content": reply})

            files = parse_files(reply)
            if not files:
                status.update(
                    label=f"Iteration {i} — could not parse files",
                    state="error",
                    expanded=True,
                )
                st.code(reply)
                st.stop()

            write_files(files)
            passed, log = run_validation()

            render_summary_line(log)
            with st.expander("View generated code", expanded=False):
                render_files(files)
            with st.expander("View full validation output", expanded=False):
                st.code(log, language="text")

            if passed:
                status.update(
                    label=f"Iteration {i} — passed", state="complete", expanded=True
                )
                passed_on = i
                break

            # Collapse this iteration now that we're moving on to a retry,
            # so only the current/final iteration stays open on screen.
            status.update(
                label=f"Iteration {i} — failed, retrying",
                state="error",
                expanded=False,
            )
            current_task = (
                "The previous solution failed validation. Fix the code so it "
                f"passes. Here is the validation output:\n\n{log}"
            )

    if passed_on:
        st.success(f"Validation passed on iteration {passed_on}.")
    else:
        st.error(f"Did not pass validation within {MAX_ITERATIONS} iterations.")
