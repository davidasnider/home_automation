"""Utilities modules that are common to many scripts and modules"""
import os
import smtplib
from email.message import EmailMessage
from xmlrpc.client import Boolean

import requests
from requests.auth import HTTPDigestAuth

# Get some variables from the environment
indigo_username = os.getenv("indigo_username")
indigo_password = os.getenv("indigo_password")

# Contains utilities that will be used across home automation scripts.

# Mail function


def send_email(address: str, subject: str, msgBody):
    """Sends an email to yourself

    This is intentionally going to send the email to the same address that it
    is sent from. Not designed to be a general purpose email sender. It is only
    used for notifications coming from our automation system.

    Parameters
    ----------
    address : str
        Email address to send the to, as well as from.
    subject : str
        What should the email subject be?
    msgBody : str
        What will be displayed in the email body?
    """
    message = EmailMessage()
    message.set_content(msgBody, subtype="html")
    message.add_alternative(msgBody, subtype="html")
    message["From"] = address
    message["To"] = address
    message["Subject"] = subject

    s = smtplib.SMTP(host="mail.thesniderpad.com", port=2525)
    s.send_message(message)
    s.quit


# Update Indigo Function
def update_indigo_variable(variable: str, payload) -> Boolean:
    """Updates the Indigo server variable with a defined value

    Parameters
    ----------
    variable : str
        The name of the variable to be updated
    payload : Any
        What should the new value of the variable be?

    Returns
    -------
    Boolean
        True if successful, False if not.
    """

    # this function updates variables in Indigo.  It probably should validate that they exist first
    url = (
        "http://blanc.thesniderpad.com:8000/variables/"
        + variable
        + "?_method=put&value="
        + str(payload)
    )
    r = requests.get(url, auth=HTTPDigestAuth(indigo_username, indigo_password))
    return r.ok


def get_indigo_variable(variable: str):
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
    url = f"http://blanc.thesniderpad.com:8000/variables/{variable}.json"
    r = requests.get(url, auth=HTTPDigestAuth(indigo_username, indigo_password))
    if r.ok:
        return_value = r.json()["value"]
        return return_value
