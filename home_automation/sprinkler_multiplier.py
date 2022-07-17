"""Module for dealing with sprinkler automation, specifically the multiplier."""
import inspect
import json
import sys
import tempfile
import time
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Any, Optional

import markdown
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from pydantic import BaseModel, validator
from tabulate import tabulate

from home_automation import utilities

settings = utilities.Settings()


class sprinkler_multiplier(BaseModel):
    """
    A class used to generate the sprinkler multiplier report as well as update
    our home automation system.

    Attributes
    ----------
    location: str
        The Tomorrow.io location ID, found in the developer console. Set via
        an environment variable: tmrw_location_id
    api_key: str
        The Tomorrow.io API key, found in the developer console. Set via an
        environment variable: tomorrow_io
    my_report: Any

    Methods
    -------
    validate_is_not_none(v: Any)
        Validate that the value is not None, if None, raise a ValueError
    """

    location: str = settings.tmrw_location_id
    api_key: str = settings.tomorrow_io
    my_report: Optional[Any] = None
    my_report_html: str = ""
    _forecast: Optional[dict]
    _forecast_df: Any
    _forecast_averages: Any
    _forecast_rain: int = 0  # Default to zero, no rain
    _value: int = 0  # Default to zero, we don't water
    _chart_png = tempfile.NamedTemporaryFile(
        delete=False
    ).name  # Just the temp filename is all we need

    # Anything with an underscore is a private attribute by default
    class Config:
        """Sets configuration for the BaseModel class"""

        underscore_attrs_are_private = True

    # We need to make sure these variables are not NONE (they don't exist)
    # before we run the rest of the functions.
    @validator("location", "api_key", always=True)
    def validate_is_not_none(cls, v):
        """Ensures that passed in attributes are not None

        This is a custom validator used in Pydantic to ensure that both the
        location and api_key are not None during class instantiation. These
        are fed from an environment variable which will return None if not
        set, therefore the validation is necessary. If the values are None,
        the validator will raise a ValueError.

        Parameters
        ----------
        v : Any
            The variable to validate is not None

        Returns
        -------
        v : Any
            Will return whatever is passed in if it is not None

        Raises
        ------
        ValueError
            Informs the user that the environment variable is not set
        """
        if v is None:
            raise ValueError("Environment variable not set")
        return v

    # Get latest measurements
    def update_data(self):
        """Retrieve the latest measurements from Tomorrow.io"""
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

        give_up_after_tries = 3  # We should try 3 times, due to rate limiting
        current_tries = 0
        while current_tries < give_up_after_tries:
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

                # Calculate the average temperature for the next 5 days
                self._forecast_averages = self._forecast_df[["Temp"]].head(5).mean()

                # Just get the first 3 days of rain accumulation
                self._forecast_rain = self._forecast_df[["Rain (in)"]][0:3].sum()[
                    "Rain (in)"
                ]
                break  # Successful data pull, break out of the loop
            elif response.status_code == 429:
                print(f"Retry after {response.headers['Retry-After']} seconds")
                # Sleep for how long the Retry-After header tells us, plus one second
                time.sleep(int(response.headers["Retry-After"]) + 1)
            else:
                print("Get forecast failed, error: ", response.text)
                sys.exit(255)
            current_tries += 1  # Count the loop traversal

        if current_tries == give_up_after_tries:
            print("Exceeded retries, exiting.")
            sys.exit(1)  # no data, fail

    def calc_multiplier(self):
        """Calculate the sprinkler multiplier for home automation system"""

        self.update_data()  # First lets update the forecast data

        # Setup a list of tuples for ranges, home automation system has the
        # logic to what a 1, 2, 3, or 4 mean. Basically, it's typically the
        # number of days to water. Temp ranges in F
        ranges = [
            (-99, 70),  # We don't water here
            (70, 80),  # We set to 1 day a week
            (80, 90),  # We set to 2 days a week
            (90, 100),  # We set to 3 days a week
            (100, 200),  # It's damn hot... turn on a 4th day
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
        """Returns the multiplier value that has been calculated"""
        return self._value  # This should return the sprinkler multiplier value

    @property
    def rain(self):
        """Returns the amount of calculated rain"""
        return self._forecast_rain  # Tell us the amount of rain in next 3 days

    def text_report(self):
        """Prints a simple table of the multiplier report"""
        headers = ["Measurement", "Value"]
        data = [
            ["Temp", self._forecast_averages["Temp"]],
            ["Rain", self.rain],
            ["Multiplier", self.value],
        ]

        return tabulate(data, headers=headers)

    def get_chart(self):
        """Returns a png of a matplotlib figure of the multiplier report"""
        df = self._forecast_df
        fig, ax1 = plt.subplots()
        ax1.plot(df.index, df.Temp, marker="o", color="green")
        ax1.set_ylim(0, 110)
        ax1.set_ylabel("Temperature (F)", color="green")
        ax1.legend(["Temp"], loc="upper left")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

        ax2 = ax1.twinx()
        ax2.set_ylim(0, 1)
        ax2.set_ylabel("Rain (in)", color="blue")
        ax2.bar(df.index, df["Rain (in)"], color="blue")
        ax2.legend(["Rain"], loc="upper right")
        fig.savefig(self._chart_png, format="png")

    def get_email_message(self) -> EmailMessage:
        """Returns an email message with the multiplier report

        Returns
        -------
        EmailMessage: A python email message object ready to send
        """
        graph_cid = make_msgid()
        markdown_text = f"""
        ## Sprinkler multiplier report
        ![graph](cid:{graph_cid[1:-1]})

        | | Value |
        | :--- | ---: |
        | Temp | {self._forecast_averages['Temp']:.2f} |
        | Rain | {self.rain:.2f} |
        | Multiplier | {self.value} |
        """
        markdown_html = markdown.markdown(
            inspect.cleandoc(markdown_text), extensions=["tables"]
        )
        pretty_html = utilities.make_pretty_html(markdown_html.strip())

        msg = EmailMessage()
        msg["Subject"] = "Sprinkler multiplier report"
        msg["From"] = settings.email_from
        msg["To"] = settings.email_to
        msg.set_content(self.text_report())
        msg.add_alternative(pretty_html, subtype="html")

        with open(self._chart_png, "rb") as img:
            msg.get_payload()[1].add_related(img.read(), "image", "png", cid=graph_cid)

        return msg
