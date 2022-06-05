"""Tests for the sprinkler multiplier module"""
import pandas
import pytest

from home_automation import sprinkler_multiplier


@pytest.fixture
def my_class():
    """Pytest fixture that returns the sprinkler_multiplier object

    Returns
    -------
    sprinkler_multiplier.sprinkler_multiplier
        The sprinkler multiplier object
    """
    my_class = sprinkler_multiplier.sprinkler_multiplier()
    my_class.calc_multiplier()
    return my_class


def test_environment_variables(my_class):
    """Ensure that the environment variables are set

    Parameters
    ----------
    my_class : sprinkler_multiplier.sprinkler_multiplier
        The pytest fixture in which the tests will be performed
    """
    assert my_class.api_key is not None
    assert my_class.location is not None


def test_get_update_data(my_class):
    """Pull the data and ensure that some of the objects are of the instance type
    we were expecting.

    Parameters
    ----------
    my_class : sprinkler_multiplier.sprinkler_multiplier
        The pytest fixture in which the tests will be performed
    """
    assert isinstance(my_class._forecast, dict)
    assert isinstance(my_class._forecast_averages, pandas.core.series.Series)


def test_calc_multiplier(my_class):
    """Thest that our object has a multiplier value and that it is an int. Also
    ensure that it has a non zero value.

    Parameters
    ----------
    my_class : sprinkler_multiplier.sprinkler_multiplier
        The pytest fixture in which the tests will be performed
    """
    assert isinstance(my_class.value, int)
    assert my_class.value >= 0


def test_calc_rain_sum(my_class):
    """Thest that our object has a rain value and that it has a non zero value.

    Parameters
    ----------
    my_class : sprinkler_multiplier.sprinkler_multiplier
        The pytest fixture in which the tests will be performed
    """
    assert my_class.rain >= 0
