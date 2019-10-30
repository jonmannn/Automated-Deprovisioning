import json
import os
import base64
import datetime as dt
import dateutil
import logging

import apiclient
import httplib2

from botocore.exceptions import ClientError
from google.oauth2 import service_account
from google.auth import impersonated_credentials
from google.auth.transport.requests import AuthorizedSession
from oauth2client.service_account import ServiceAccountCredentials

# TODO: Lookup key names for these attributes
gsuite_creds = [ 'key': 'value,
                'key': 'value']

# Username of user with API access (usually a service account)
api_user = "service_account@example.com"

# Place target org unit here
org_unit = "/offboarding ou/Automated Offboarding"

# Authenticate into GSuite with API access
def get_gsuite_credentials():
    keys = gsuite_creds
    keys_dict = json.loads(keys)
    scopes = 'https://www.googleapis.com/auth/admin.directory.user'

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=keys_dict, scopes=scopes)
    credentials = credentials.create_delegated(api_user)

    return apiclient.discovery.build('admin', 'directory_v1', credentials=credentials)

def deprovision_GSuite(email):
    directory = get_gsuite_credentials()
    try:
        action = directory.users().update(
        userKey=email,
        body={'orgUnitPath': org_unit}, ).execute()
        return "Success"
    except apiclient.errors.HttpError:
        return "Failure: A user with this GSuite email address was not found"


def __main__():
    # TODO: Figure out how to populate this as an env
    email = input("Please input the departing user's email address: ")
    gsuite_result = deprovision_GSuite(email)
    print(gsuite_result)

