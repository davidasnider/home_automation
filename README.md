# Home Automation Scripts for the SniderPad

## Getting Started

Clone the repository, and runf `make setup-dev` to configure your development
environment.

Copy the `.env_template` to `.env` and update the variables with the proper
values.

Run `poetry shell` followed by `pytest -s -v` to validate your environment and
setup.

## Sprinkler Multiplier

This script uses weather data from Tomorrow.io to calculate the average high
temperature and then update our Indigo Server with the appropriate measure.
Finally, send an email with charts and data.
