# Project Conversation Guidelines
1. Use `uv` to manage python dependencies and `pyproject.toml` for dependency management.
2. Use `source .venv/bin/activate` to activate the virtual environment.
3. Use `pytest` for unit testing.
4. Use `pre-commit` for code formatting and linting before committing. Can skip `mypy` check by adding `--no-verify` to the commit command.
5. Use `terraform` for infrastructure as code and follow below commands to check syntax:
   - `terraform fmt -check -recursive`
   - `terraform validate`
   - `terraform plan --var-file="<var_file>" -out="tfplan.binary"`
   - `terraform apply "tfplan.binary"`
