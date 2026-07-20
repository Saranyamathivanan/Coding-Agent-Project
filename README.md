Mini AI Coding Agent

The Mini AI Coding Agent is a Python prototype that uses Anthropic’s Claude API to generate code, validate it automatically, and correct errors using real validation feedback.

How it works
The user describes a coding task.
Claude generates a Python solution and matching pytest tests.
The agent validates the files using:
Python ast for syntax
pytest for correctness
Flake8 for code quality and style
If validation fails, the exact errors are returned to Claude.
Claude corrects the code and validation runs again.
This continues for up to four attempts or until all checks pass.

Generated code follows predefined standards, including PEP 8, type hints, docstrings, no bare except statements, and no unsupported characters.

Project files
coding_agent.py – Manages code generation, file creation, validation and correction.
streamlit_app.py – Provides a browser interface with task input, iteration progress and results.
requirements.txt – Contains the required Python packages.
Setup
pip install -r requirements.txt

Set the Anthropic API key:

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-..."

Never save the API key in the source code or upload it to GitHub.

Run

Command line:

python coding_agent.py

Run a custom task:

python coding_agent.py "Write a function that merges overlapping time intervals"

Browser interface:

streamlit run streamlit_app.py
Testing

The agent has been tested with palindrome checking, prime-number checking, email validation, volume-discount calculation and time-interval merging.

During testing, some initial solutions failed because of coding or style errors. The agent used the validation output to correct them, and the revised versions passed successfully.

Limitations
Generated code runs locally without sandboxing or human approval.
Only Python solution and test files are supported.
File extraction uses regex markers instead of Claude’s tool-use API.
Coding standards are currently fixed.
Multi-file projects are not supported.
Future improvements
Use Claude’s tool-use API
Support configurable company standards
Add mypy and security scanning
Track API costs
Run generated code in a secure sandbox
Support multiple files and programming languages
Add GitHub and CI/CD integration
