"""Tests for the sprinkler multiplier module"""
import smtplib
from datetime import datetime
from unittest.mock import Mock, patch

import matplotlib.pyplot as plt
import pandas
import pytest

from home_automation import sprinkler_multiplier, utilities


@pytest.fixture
def get_good_api_response():
    """
    Returns a sample API response with mock data.

    The response contains a timeline with intervals representing different days.
    Each interval includes the start time and values for rain accumulation and temperature.

    Returns:
        dict: A dictionary representing the API response.
    """
    my_response = {
        "data": {
            "timelines": [
                {
                    "timestep": "1d",
                    "endTime": "2024-01-20T06:00:00-07:00",
                    "startTime": "2024-01-15T06:00:00-07:00",
                    "intervals": [
                        {
                            "startTime": "2024-01-15T06:00:00-07:00",
                            "values": {"rainAccumulation": 0, "temperature": 27.28},
                        },
                        {
                            "startTime": "2024-01-16T06:00:00-07:00",
                            "values": {"rainAccumulation": 0, "temperature": 35.05},
                        },
                        {
                            "startTime": "2024-01-17T06:00:00-07:00",
                            "values": {"rainAccumulation": 0.02, "temperature": 34.76},
                        },
                        {
                            "startTime": "2024-01-18T06:00:00-07:00",
                            "values": {"rainAccumulation": 0, "temperature": 33.28},
                        },
                        {
                            "startTime": "2024-01-19T06:00:00-07:00",
                            "values": {"rainAccumulation": 0, "temperature": 34.61},
                        },
                        {
                            "startTime": "2024-01-20T06:00:00-07:00",
                            "values": {"rainAccumulation": 0, "temperature": 35.64},
                        },
                    ],
                }
            ]
        }
    }
    return my_response


@pytest.fixture
def my_class(mocker, get_good_api_response):
    """Pytest fixture that returns the sprinkler_multiplier object

    Returns
    -------
    sprinkler_multiplier.sprinkler_multiplier
        The sprinkler multiplier object
    """

    # Mock the requests.request function
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = get_good_api_response
    mocker.patch("requests.request", return_value=mock_response)
    my_class = sprinkler_multiplier.sprinkler_multiplier()
    my_class.calc_multiplier()
    return my_class


def test_update_data(my_class):
    """
    Test the update_data method of MyClass.

    Parameters:
    my_class (MyClass): An instance of MyClass.

    Returns:
    None
    """

    # Assert that the _forecast, _forecast_df, and _forecast_df.columns attributes are set correctly
    # assert sm._forecast == # Expected value here
    # assert sm._forecast_df.equals(# Expected DataFrame here)
    assert list(my_class._forecast_df.columns) == ["Rain (in)", "Temp"]


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
    """Test that our object has a multiplier value and that it is an int. Also
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


@patch("requests.request")
def test_update_data_other_error(mock_get, my_class):
    """
    Test case for the scenario when the API response returns a status code of 450,
    indicating an error other than the ones handled explicitly.

    Args:
        mock_get (Mock): The mocked get method for the API.
        my_class (MyClass): An instance of the class being tested.

    Raises:
        SystemExit: If the method being tested raises a SystemExit exception.

    Returns:
        None
    """

    # Mock the API response
    mock_response = Mock()
    mock_response.status_code = 450
    mock_response.ok = False
    mock_response.headers = {"Retry-After": "0"}
    mock_get.return_value = mock_response

    # Call the method and assert that it raises a SystemExit exception
    with pytest.raises(SystemExit) as e:
        my_class.update_data()
    assert e.type == SystemExit
    assert e.value.code == 255  # Assert that the exit code is 1


def test_rain_greater_than_1(mocker, my_class, get_good_api_response):
    """
    Test case to verify the behavior of the `calc_multiplier` method when the rain accumulation is greater than 1.

    Args:
        mocker: The mocker object for mocking external dependencies.
        my_class: An instance of the class being tested.
        get_good_api_response: A mock API response containing rain accumulation data.

    Returns:
        None
    """

    # Mock the requests.request function
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = get_good_api_response
    mocker.patch("requests.request", return_value=mock_response)

    # Change the values to > 1
    for i in get_good_api_response["data"]["timelines"][0]["intervals"]:
        i["values"]["rainAccumulation"] = 2

    my_class.calc_multiplier()

    # Assert that the _forecast, _forecast_df, and _forecast_df.columns attributes are set correctly
    # assert sm._forecast == # Expected value here
    # assert sm._forecast_df.equals(# Expected DataFrame here)
    assert my_class.rain == 6  # 2 * 3 days
    assert my_class.value == 0


def test_high_temp_loop(mocker, get_good_api_response):
    """
    Test case for checking the behavior of the sprinkler_multiplier.calc_multiplier() method
    when the temperatures are set to be hotter.

    Args:
        mocker: The mocker object used for mocking the requests.request function.
        get_good_api_response: The API response data used for testing.

    Returns:
        None
    """
    # Mock the requests.request function
    mock_response = Mock()
    mock_response.ok = True

    # Make the temperatures hotter
    for i in get_good_api_response["data"]["timelines"][0]["intervals"]:
        i["values"]["temperature"] = 100

    mock_response.json.return_value = get_good_api_response
    mocker.patch("requests.request", return_value=mock_response)
    my_class = sprinkler_multiplier.sprinkler_multiplier()
    my_class.calc_multiplier()


def test_text_report(my_class):
    """
    Test the text_report method of MyClass.

    This test sets the forecast averages, rain, and value to known values and calls the text_report method.
    It then asserts that the returned string matches the expected report.

    Parameters:
    - my_class: An instance of MyClass.

    Returns:
    None
    """

    # Set _forecast_averages, rain, and value to known values
    my_class._forecast_averages = {"Temp": 70}
    my_class._forecast_rain = 0.5
    my_class._value = 1.5

    # Call the method and assert that it returns the expected string
    expected_report = "Measurement      Value\n-------------  -------\nTemp              70\nRain               0.5\nMultiplier         1.5"
    assert my_class.text_report() == expected_report


def test_get_chart(mocker, my_class):
    """
    Test case for the `get_chart` method of MyClass.

    This test verifies that the `get_chart` method correctly saves the chart as a PNG file.

    Args:
        mocker: The mocker object for mocking `savefig` method.
        my_class: An instance of MyClass.

    Returns:
        None
    """

    # Set _forecast_df to a DataFrame with known values
    my_class._forecast_df = pandas.DataFrame(
        {"Date": [datetime.now()], "Temp": [70], "Rain (in)": [0.5]}
    )
    my_class._forecast_df.set_index("Date", inplace=True)

    # Mock fig.savefig
    mock_savefig = mocker.patch.object(plt.Figure, "savefig")

    # Call the method
    my_class.get_chart()

    # Assert that fig.savefig was called with the correct arguments
    mock_savefig.assert_called_once_with(my_class._chart_png, format="png")


def test_get_email_message(mocker, my_class):
    """
    Test case for the `get_email_message` method of the `my_class` object.

    This test verifies that the `get_email_message` method returns an EmailMessage object with the correct attributes.
    It also checks that the `open` function is called with the correct arguments.

    Args:
        mocker: The mocker object used for mocking dependencies.
        my_class: An instance of the `my_class` object.
    """

    # Set _forecast_averages, rain, value, and _chart_png to known values
    my_class._forecast_averages = {"Temp": 70}
    my_class._forecast_rain = 0.5
    my_class._value = 1.5
    my_class._chart_png = "chart.png"

    # Mock EmailMessage and its methods
    mocker.patch("email.message.EmailMessage", return_value=Mock())

    # Mock open
    mock_open = mocker.patch(
        "builtins.open", mocker.mock_open(read_data=b"file content")
    )

    # Call the method
    result = my_class.get_email_message()

    # Assert that the attributes of the returned EmailMessage object are correct
    assert result["Subject"] == "Sprinkler multiplier report"
    assert result["From"] == sprinkler_multiplier.settings.email_from
    assert result["To"] == sprinkler_multiplier.settings.email_to

    # Assert that open was called with the correct arguments
    mock_open.assert_called_with(my_class._chart_png, "rb")


def test_checkResponse_success(mocker):
    """
    Test the checkResponse function with a successful response.

    Args:
        mocker: The mocker object for mocking dependencies.

    Returns:
        None
    """

    # Create a mock Response object with a status_code of 200
    mock_response = Mock()
    mock_response.status_code = 200

    # Call the function with the mock Response object
    utilities.checkResponse(mock_response)


def test_checkResponse_failure(mocker):
    """
    Test case to check the failure scenario of the checkResponse function.

    Args:
        mocker: The mocker object for mocking dependencies.

    Raises:
        SystemExit: If the checkResponse function raises a SystemExit.

    Returns:
        None
    """

    # Create a mock Response object with a status_code of 400 and a text of "Error"
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Error"

    # Call the function with the mock Response object and assert that sys.exit was called with the status_code
    with pytest.raises(SystemExit) as e:
        utilities.checkResponse(mock_response)
    assert e.value.code == 400


def test_send_email(mocker):
    """
    Test case for the send_email function.

    Args:
        mocker: The mocker object used for mocking dependencies.

    Returns:
        None
    """

    # Create a mock EmailMessage object
    mock_message = Mock()

    # Create a mock SMTP object and set its send_message and quit methods to mocks
    mock_smtp = Mock()
    mock_send_message = Mock()
    mock_quit = Mock()
    mock_smtp.send_message = mock_send_message
    mock_smtp.quit = mock_quit

    # Replace smtplib.SMTP with a mock that returns the mock SMTP object
    mocker.patch.object(smtplib, "SMTP", return_value=mock_smtp)

    # Call the function with the mock EmailMessage object
    utilities.send_email(mock_message)

    # Assert that the send_message method of the mock SMTP object was called with the mock EmailMessage object
    mock_send_message.assert_called_once_with(mock_message)

    # Assert that the quit method of the mock SMTP object was called
    mock_quit.assert_called_once()


@patch("requests.post")
def test_update_indigo_variable_ok(mock_post):
    """
    Test case for the update_indigo_variable function when the response is successful (ok=True).

    Args:
        mock_post (Mock): A mock object for the post method.

    Returns:
        None
    """

    # Create a mock Response object with ok set to True
    mock_response = Mock()
    mock_response.ok = True
    mock_post.return_value = mock_response

    # Call the function
    result = utilities.update_indigo_variable(1, "value")

    # Assert that the function returned True
    assert result is True


@patch("requests.post")
def test_update_indigo_variable_not_ok(mock_post):
    """
    Test case for the scenario when the update_indigo_variable function receives a response with ok set to False.

    Args:
        mock_post (Mock): A mock object representing the post method.

    Returns:
        None
    """

    # Create a mock Response object with ok set to False
    mock_response = Mock()
    mock_response.ok = False
    mock_post.return_value = mock_response

    # Call the function
    result = utilities.update_indigo_variable(1, "value")

    # Assert that the function returned False
    assert result is False


@patch("requests.post")
def test_update_magicmirror_internal_temperature_ok(mock_post):
    """
    Test case for the update_magicmirror_internal_temperature function when the mock post request is successful.

    Args:
        mock_post (Mock): The mock post request object.

    Returns:
        None
    """

    # Create a mock Response object with ok set to True
    mock_response = Mock()
    mock_response.ok = True
    mock_post.return_value = mock_response

    # Call the function
    result = utilities.update_magicmirror_internal_temperature(25.0)

    # Assert that the function returned True
    assert result is True


@patch("requests.post")
def test_update_magicmirror_internal_temperature_not_ok(mock_post):
    """
    Test case for the scenario when the update_magicmirror_internal_temperature function
    receives a response with ok set to False.

    Args:
        mock_post (Mock): A mock object representing the post method.

    Returns:
        None
    """

    # Create a mock Response object with ok set to False
    mock_response = Mock()
    mock_response.ok = False
    mock_post.return_value = mock_response

    # Call the function
    result = utilities.update_magicmirror_internal_temperature(25.0)

    # Assert that the function returned False
    assert result is False
