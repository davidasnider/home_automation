setup-dev:
	rm -rf .venv;
	python3 -m venv .venv
	poetry install
	pre-commit install
