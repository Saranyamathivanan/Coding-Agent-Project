Mini AI Coding Agent

The Mini AI Coding Agent is a small prototype I built to understand how an AI coding agent works in practice. It uses Anthropic’s Claude API to generate Python code, test the generated solution automatically, and correct it when something goes wrong.

Instead of asking a person to copy an error message and send it back to Claude, the agent handles this process itself. It takes the actual output from testing and code-quality tools, gives that feedback to Claude, and asks it to produce an improved version.

How it works
The user describes a coding task in plain English.

Claude generates:

A Python solution file
A matching pytest test file

The generated code must follow a fixed set of standards, including PEP 8 formatting, type hints, docstrings, no bare except statements, and no emoji or unsupported characters.

The agent saves the generated files and validates them automatically.

Python’s ast module checks the files for syntax errors.
If the syntax is valid, pytest runs the generated tests.
Flake8 checks the code for formatting and style problems.

The syntax check is performed first so that the user receives a short and useful error message instead of a long pytest collection traceback.

If any validation check fails, the agent sends the exact error output back to Claude. Claude reviews the feedback and generates corrected files.
The process repeats until the solution passes validation or reaches the maximum limit of four attempts.
Project structure
coding_agent.py

This is the main part of the project. It:

Connects to the Claude API
Sends the user’s task and coding standards to Claude
Extracts the generated solution and test files
Writes the files to disk
Runs syntax, pytest and Flake8 checks
Sends validation errors back to Claude
Controls the generate–validate–correct cycle

The agent can be run directly from the command line.

streamlit_app.py

This file provides an optional browser interface for the agent. It reuses the functions from coding_agent.py, so the main logic is not duplicated.

The interface includes:

A text box for entering a coding task
A Run agent button
Live progress for each attempt
A validation summary
Tabs for viewing the generated solution and tests
Expandable sections containing detailed validation output
requirements.txt

This file contains the project dependencies:

anthropic
pytest
flake8
streamlit
Installation

Install the required packages:

pip install -r requirements.txt

Set your Anthropic API key in the terminal before running the project.

Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
macOS or Linux
export ANTHROPIC_API_KEY="sk-ant-..."

Keep the API key private. It should not be placed directly in the source code or uploaded to GitHub.

Running the agent

Run the command-line version with the default palindrome-checker task:

python coding_agent.py

To provide your own task:

python coding_agent.py "Write a function that merges overlapping time intervals"

To start the browser interface:

streamlit run streamlit_app.py

Streamlit will normally open the application at:

http://localhost:8501
Testing completed

I tested the agent with several tasks, including:

Checking whether a word is a palindrome
Identifying prime numbers
Validating email addresses
Calculating tiered volume discounts
Merging overlapping time intervals

During testing, some initial solutions failed because of programming errors or Flake8 style violations. The agent captured the validation output, returned it to Claude, and requested a correction. In multiple cases, the corrected solution passed successfully on the second attempt.

This generate–fail–correct–pass workflow is the main behaviour demonstrated by the project. It shows that the agent is not limited to generating code that works only on its first attempt.

Current limitations

This is an early personal prototype, so it has several limitations:

Generated code is written to disk and executed without human review. This may be acceptable for a small local experiment, but it would not be safe for a public or production system without sandboxing and approval controls.
The agent uses ### FILE: filename markers and regular expressions to extract files from Claude’s response. Anthropic’s tool-use API would provide a more reliable structured-output method.
Each task supports only one solution file and one test file.
The agent currently supports Python only.
Coding standards are fixed rather than configurable for different organisations.
The validation pipeline does not yet include static type checking or advanced security scanning.
Possible improvements

Future development could include:

Using Claude’s tool-use API for structured file generation
Supporting configurable company-specific coding standards
Adding mypy for static type checking
Adding security checks such as Bandit
Tracking API usage and cost for each run
Running generated code inside a secure sandbox
Supporting multi-file applications
Adding more programming languages
Requiring human approval before executing or accepting generated code
Integrating the agent with GitHub and CI/CD pipelines

This prototype provides a practical foundation for a more advanced AI coding agent that could eventually generate and validate code according to the standards and development practices of different organisations.
