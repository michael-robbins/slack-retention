#!/usr/bin/python

from datetime import datetime, timedelta

import requests
import calendar
import argparse
import json
import sys

SLACK_FILES_DELETE_API_ENDPOINT = "https://{domain}.slack.com/api/files.delete"

def call_slack_api(url, payload):
    response = requests.post(url, payload)

    if response.status_code != 200:
        raise RuntimeError("Slack API didn't return a 200 status code")

    response = response.json()

    if not response["ok"]:
        raise RuntimeError("Slack API errored with: {0}".format(response["error"]))

    return response

def get_user_id(username, token):
    response = call_slack_api("https://slack.com/api/users.list", {"token": token})

    for member in response["members"]:
        if member["name"] == username:
            return member["id"]

    return None

def get_user_files(user_id, token, filter_types, days_ago):
    realised_days_ago = str(calendar.timegm((datetime.now() - timedelta(days_ago)).utctimetuple()))

    payload = {"token": token, "user": user_id, "ts_to": realised_days_ago, "types": filter_types}
    response = call_slack_api("https://slack.com/api/files.list", payload)

    return response["files"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-token", required=True, help="Your Slack API Token obtained from: https://api.slack.com/custom-integrations/legacy-tokens")
    parser.add_argument("--username", required=True, help="Your Slack username (used to find your files to delete)")
    parser.add_argument("--filter-types", default="snippets,spaces,images,gdocs,zips,pdfs", help="List of file types we will delete, found here: https://api.slack.com/methods/files.list")
    parser.add_argument("--cutoff-days", default=3, type=int, help="Number of days from today that we will leave alone (defaults to 3)")
    args = parser.parse_args()

    # Get the user's ID, so we can filter down the files to just theirs
    user_id = get_user_id(args.username, args.api_token)

    # Get the files associated to that user older than the cutoff (default to 3 days)
    files = get_user_files(user_id, args.api_token, args.filter_types, args.cutoff_days)

    if len(files) == 0:
        print("INFO: No files returned from this user")
        sys.exit(0)

    # Delete all returned files!
    for f in files:
        print("Deleting file {0}".format(f["name"]))
        response = call_slack_api("https://slack.com/api/files.delete", {"token": args.api_token, "file": f["id"]})

