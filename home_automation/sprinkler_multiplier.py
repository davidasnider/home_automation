import json
import os
from typing import Any, Optional

import pandas as pd
import requests
from pydantic import BaseModel, validator

from tabulate import tabulate

pd.set_option("plotting.backend", "pandas_bokeh")

# Class contains all the code for generating the sprinkler multiplier report
# as well as updating our home automation system.


class sprinkler_multiplier(BaseModel):

    location: str = os.getenv("tmrw_location_id")
    api_key: str = os.getenv("tomorrow_io")
    my_report: Optional[Any] = None
    my_report_html: str = ""
    _forecast: Optional[dict]
    _forecast_df: Any
    _forecast_averages: Any
    _forecast_rain: int = 0  # Default to zero, no rain
    _value: int = 0  # Default to zero, we don't water

    # Anything with an underscore is a private attribute by default
    class Config:
        underscore_attrs_are_private = True

    # We need to make sure these variables are not NONE (they don't exist)
    # before we run the rest of the functions.
    @validator("location", "api_key", always=True)
    def validate_is_not_none(cls, v):
        if v is None:
            raise ValueError("Environment variable not set")
        return v

    # Get latest measurements
    def update_data(self):
        url = "https://api.tomorrow.io/v4/timelines"
        payload = {
            "units": "imperial",
            "location": self.location,
            "timesteps": ["1d"],
            "fields": ["temperature", "rainAccumulation"],
            "timezone": "America/Denver",
        }

        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

        response = requests.request(
            "POST", url, data=json.dumps(payload), headers=headers
        )
        if response.ok:
            self._forecast = response.json()
            self._forecast_df = pd.json_normalize(
                self._forecast["data"]["timelines"][0]["intervals"]
            )
            # Make the column names friendly
            self._forecast_df.columns = ["Date", "Rain (in)", "Temp"]

            # Convert dates and make date the index
            self._forecast_df["Date"] = pd.to_datetime(
                self._forecast_df["Date"]
            ).dt.date

            # Change the index to the date time
            self._forecast_df = self._forecast_df.set_index("Date")

            # Calculate the average temperature
            self._forecast_averages = self._forecast_df[["Temp"]].mean()

            # Just get the first 3 days of rain accumulation
            self._forecast_rain = self._forecast_df[["Rain (in)"]][0:3].sum()[
                "Rain (in)"
            ]
        else:
            print("Get forecast failed, error: ", response.text)

    # Calculate the sprinkler multiplier for home automation system
    def calc_multiplier(self):

        self.update_data()  # First lets update the forecast data

        # Setup a list of tuples for ranges, home automation system has the
        # logic to what a 1, 2, 3, or 4 mean. Basically, it's typically the
        # number of days to water. Temp ranges in F
        ranges = [
            (-99, 70),  # We don't water here
            (70, 80),  # We set to 1 here
            (80, 90),  # We set to 2 here
            (90, 200),  # We set to 3 here
        ]

        # Are we getting lots of rain? Just set it to zero overall
        if self.rain > 1:
            # We are getting an inch of rain in the next few days
            self._value = 0
        else:  # Not enough rain, lets get the temperature based value
            x = 0  # counter for index
            for range in ranges:
                min = range[0]
                max = range[1]

                if (
                    self._forecast_averages["Temp"] > min
                    and self._forecast_averages["Temp"] <= max
                ):
                    self._value = x
                    break  # Process no more values.
                x = x + 1

    @property
    def value(self):
        return self._value  # This should return the sprinkler multiplier value

    @property
    def rain(self):
        return self._forecast_rain  # Tell us the amount of rain in next 3 days

    def report(self):
        # Create a datastructure to print
        headers = ["Measurement", "Value"]
        data = [
            ["Temp", self._forecast_averages["Temp"]],
            ["Rain", self.rain],
            ["Multiplier", self.value],
        ]

        print(tabulate(data, headers=headers))
