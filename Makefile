setup-dev:
	rm -rf .venv;
	python3 -m venv .venv
	poetry install
	pre-commit install

requirements:
	poetry export -f requirements.txt --output requirements.txt

run-tests:
	poetry run pytest -s -v
