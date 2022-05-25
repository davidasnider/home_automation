import os
from xmlrpc.client import Boolean
import requests
from requests.auth import HTTPDigestAuth
from email.message import EmailMessage
import smtplib

# Get some variables from the environment
indigo_username = os.getenv("indigo_username")
indigo_password = os.getenv("indigo_password")

# Contains utilities that will be used across home automation scripts.

# Mail function


def send_email(address, subject, msgBody):
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
def update_indigo_variable(variable, payload) -> Boolean:

    # this function updates variables in Indigo.  It probably should validate that they exist first
    url = (
        "http://blanc.thesniderpad.com:8000/variables/"
        + variable
        + "?_method=put&value="
        + str(payload)
    )
    r = requests.get(url, auth=HTTPDigestAuth(indigo_username, indigo_password))
    return r.ok


def get_indigo_variable(variable):
    url = f"http://blanc.thesniderpad.com:8000/variables/{variable}.json"
    r = requests.get(url, auth=HTTPDigestAuth(indigo_username, indigo_password))
    if r.ok:
        return_value = r.json()["value"]
        return return_value
