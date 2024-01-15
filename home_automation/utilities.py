"""Utilities modules that are common to many scripts and modules"""
import json
import smtplib
import sys
from email.message import EmailMessage
from xmlrpc.client import Boolean

import requests
from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings

# Contains utilities that will be used across home automation scripts.


def checkResponse(r):
    """
    Quick logic to check the http response code.

    Parameters:
            r = http response object.
    """

    acceptedResponses = [200, 201, 203, 204]
    if r.status_code not in acceptedResponses:
        print("STATUS:", r.status_code)
        print("ERROR: ", r.text)
        sys.exit(r.status_code)


class Settings(BaseSettings):
    """Pulls in environment variables and sets them as attributes

    Attributes
    ----------
    smtp_server: str
        The SMTP server to use for sending emails.
    email_to: str
        The email address to send the email to.
    email_from: str
        The email address to send the email from.
    indigo_url: AnyHttpUrl
        The URL to the Indigo server.
    magic_mirror_url: str
        The URL to the Magic Mirror server.
    indigo_api_key: SecretStr
        The API key for the Indigo server. Necessary for authentication.
    tmrw_location_id: str
        The Tomorrow.io location ID, found in the developer console. Set via
        an environment variable: tmrw_location_id
    tomorrow_io: str
        The Tomorrow.io API key, found in the developer console. Set via an
        environment variable: tomorrow_io

    """

    smtp_server: str = "mail.thesniderpad.com"
    email_to: str = "david@davidsnider.org"
    email_from: str = "david@davidsnider.org"
    indigo_url: AnyHttpUrl = "http://blanc.thesniderpad.com:8000"
    magic_mirror_url: str = "giro.thesniderpad.com:8080"
    indigo_api_key: SecretStr
    tmrw_location_id: str
    tomorrow_io_api_key: str
    metrics_server: str = "metrics.thesniderpad.com"
    netatmo_client_id: str
    netatmo_client_secret: str
    netatmo_password: str
    netatmo_device_id: str


# Make these available in this module
SETTINGS = Settings()

# Mail function


def send_email(message: EmailMessage):
    """Sends an email to yourself

    Sends an EmailMessage object to the sniderpad smtp server

    Parameters
    ----------
    msgBody : EmailMessage
        A fully formed EmailMessage object, ready to send
    """

    s = smtplib.SMTP(host=SETTINGS.smtp_server, port=2525)
    s.send_message(message)
    s.quit()


# Update Indigo Function
def update_indigo_variable(object_id: int, value: str) -> Boolean:
    """
    Updates the value of a specified Indigo variable.

    This function sends a POST request to the Indigo API to update the value of a
    specified variable. The request payload includes the message type, the object ID
    of the variable to be updated, and the new value. The request is authenticated
    using an API key.

    Args:
        object_id (int): The object ID of the variable to be updated.
        value (str): The new value for the variable.

    Returns:
        bool: True if the update was successful, False otherwise.

    Raises:
        Exception: If the request to the Indigo API fails.
    """
    variable_update_payload = {
        "message": "indigo.variable.updateValue",
        "objectId": object_id,
        "parameters": {"value": f"{value}"},  # Variable values must be strings
    }
    headers = {"Authorization": f"Bearer {SETTINGS.indigo_api_key.get_secret_value()}"}
    r = requests.post(
        str(SETTINGS.indigo_url) + "v2/api/command",
        headers=headers,
        data=json.dumps(variable_update_payload),
    )
    if r.ok:
        # log.info(f"indigo variable updated: {object_id}")
        return True
    else:
        # log.error(f"indigo variable updated failed: {object_id}")
        return False


def get_indigo_variable(object_id: int):
    """Gets the value of an Indigo variable

    Parameters
    ----------
    variable : str
        The name of the variable to be retrieved

    Returns
    -------
    return_value: Str
        The value of the requested variable.
    """
    url = str(SETTINGS.indigo_url) + "v2/api/indigo.variables/" + str(object_id)
    headers = {"Authorization": f"Bearer {SETTINGS.indigo_api_key.get_secret_value()}"}

    r = requests.get(url, headers=headers)
    if r.ok:
        return_value = r.json()["value"]
        return return_value


def update_magicmirror_internal_temperature(temperature: float):
    """Updates the internal temperature of the MagicMirror variable

    Parameters
    ----------
    temperature : float
        The temperature to update the MagicMirror with.

    Returns
    -------
    Boolean
        True if successful, False if not.
    """
    print(f"Updating MagicMirror internal temperature: {temperature}")
    data = f"temp={temperature}".encode("utf-8")
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    url = f"http://{SETTINGS.magic_mirror_url}/indoor-temperature"
    r = requests.post(url, data=data, headers=header)
    if r.ok:
        print(f"Successfully update temperature variable to {temperature}")
    else:
        print(
            f"Failed to update temperature variable to {temperature}, error: {r.text}"
        )
    return r.ok


def make_pretty_html(html_string: str):
    """Makes HTML pretty based on Boostrap css

    Parameters
    ----------
    html_string : str
        An HTML String (minus the body and it's parent tags, head..etc)

    Returns
    -------
    html_string: str
        A string with the HTML tags formatted for a Bootstrap table. Usually
        produced via markdown `markdown.markdown(markdown_text, extensions=['tables']`
    """

    cssin = open("home_automation/css/bootstrap.min.css", "r")
    new_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <style type="text/css">
            {cssin.read()}
        </style>
    </head>
        <body>
            {html_string}
        </body>
    </html>
    """

    # Replace table with style info
    html_string = new_html.replace(
        "<table>", '<table style="width: auto;" class="table table-striped">'
    )
    return html_string
