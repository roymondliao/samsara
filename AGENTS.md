# Project Conversation Guidelines

These are **mandatory execution constraints**, not suggestions. Do NOT invent workarounds that bypass these rules.

## Python

1. **MUST** use `uv` to manage dependencies and `pyproject.toml` for dependency declarations. NEVER use `pip install` directly.
2. **MUST** activate the virtual environment before any Python command: `source .venv/bin/activate`
3. **MUST** use `pytest` to run tests. NEVER use `python -m pytest`, `$(which python3) -m pytest`, or any other raw Python invocation.
   ```
   $uv run pytest <test_file_or_directory>
   ```
4. **MUST** run `pre-commit` for code formatting and linting before committing. Can skip `mypy` check by adding `--no-verify` to the commit command.

## Infrastructure

5. **MUST** use `terraform` for infrastructure as code and follow below commands to check syntax:
   - `terraform fmt -check -recursive`
   - `terraform validate`
   - `terraform plan --var-file="<var_file>" -out="tfplan.binary"`
   - `terraform apply "tfplan.binary"`

## When a command fails or produces unexpected output

1. First check if this file already prescribes how to run it.
2. Fix the environment to match these rules (e.g., activate venv, install missing deps with `uv`).
3. NEVER invent alternative invocations to bypass the prescribed tool.
