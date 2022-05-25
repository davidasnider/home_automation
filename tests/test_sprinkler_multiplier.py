from home_automation import sprinkler_multiplier
import pandas
import pytest


@pytest.fixture
def my_class():
    my_class = sprinkler_multiplier.sprinkler_multiplier()
    my_class.calc_multiplier()
    return my_class


def test_environment_variables(my_class):
    assert my_class.api_key is not None
    assert my_class.location is not None


def test_get_update_data(my_class):
    assert isinstance(my_class._forecast, dict)
    assert isinstance(my_class._forecast_averages, pandas.core.series.Series)


def test_calc_multiplier(my_class):
    assert isinstance(my_class.value, int)
    assert my_class.value >= 0


def test_calc_rain_sum(my_class):
    assert my_class.rain >= 0
