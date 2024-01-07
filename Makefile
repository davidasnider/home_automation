setup-dev:
	rm -rf .venv;
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install poetry
	.venv/bin/poetry install
	.venv/bin/pre-commit install

requirements:
	.venv/bin/poetry export -f requirements.txt --output requirements.txt

run-tests:
	.venv/bin/poetry run pytest -s -v
