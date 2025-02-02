"""
This script imports into Strava all the *.gpx files in the dir ./data-from-tomtom-sports.
These .gpx files were exported from TomTom Sports.
See README.md for more details.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import requests


def main():
    bearer_token = get_bearer_token()
    count = 0
    for gpx_file_path in yield_gpx_file_paths():
        count += 1
        upload_new_activity(gpx_file_path, bearer_token)
        time.sleep(
            0.5
        )  # To avoid getting banned (limits: 200 requests every 15 minutes, 2,000 daily).
    print(f"\nImported activities: #{count}")


def get_bearer_token():
    data = input("Type your Bearer token if you have one: ")
    if data:
        return data

    data = input("To get a Bearer token, type your app client_id: ")
    if not data.strip():
        print("Invalid")
        sys.exit(1)
    client_id = data.strip()

    data = input("And type your app client_secret: ")
    if not data.strip():
        print("Invalid")
        sys.exit(1)
    client_secret = data.strip()

    url = f"http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://127.0.0.1&approval_prompt=force&scope=read,activity:read_all,activity:write"
    print(
        f"Now open your browser at this url, then click 'Authorize' and copy the code in the url of the final blank page:\n{url}"
    )
    data = input("Type the code you copied from the url of the final blank page: ")
    if not data.strip():
        print("Invalid")
        sys.exit(1)
    auth_code = data.strip()

    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    bearer_token = response.json().get("access_token")
    if not bearer_token:
        raise Exception("Missing 'access_token' field in JSON response")
    print(f"> You got the Bearer token: {bearer_token}")
    return bearer_token


def yield_gpx_file_paths():
    for child in (Path() / "data-from-tomtom-sports").iterdir():
        if child.suffix == ".gpx":
            yield child


def get_payload_for_gpx_file_name(file_name):
    """
    Args:
        file_name: string with format like "cycling_2018-08-04_17-16-26.gpx".
    """
    if file_name.startswith("cycling"):
        activity_type = "ride"
    elif file_name.startswith("freestyle"):
        activity_type = "walk"
    elif file_name.startswith("hiking"):
        activity_type = "hike"
    elif file_name.startswith("running"):
        activity_type = "run"
    elif file_name.startswith("snowboarding"):
        activity_type = "snowboard"
    else:
        activity_type = "workout"

    ts = file_name[
        file_name.find("_") + 1 : file_name.find(".")
    ]  # Eg. 2018-08-04_17-16-26.
    ts = datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S")
    if ts.hour < 11:
        name = "Morning"
    elif ts.hour < 14:
        name = "Lunch"
    elif ts.hour < 19:
        name = "Afternoon"
    else:
        name = "Evening"
    name += f" {activity_type.capitalize()}"

    payload = {
        "activity_type": activity_type,
        "name": name,
        "description": "Batch upload from TomTom Sport (Python script)",
        "data_type": "gpx",
    }
    return payload


def upload_new_activity(gpx_file_path, bearer_token):
    """
    Upload a new activity to Strava.

    Request:
        $ curl -X POST https://www.strava.com/api/v3/uploads \
        -H "Authorization: Bearer b88eb6..." \
        -F activity_type="ride" \
        -F name="Afternoon Ride" \
        -F description="Batch upload from TomTom Sport (Python script)" \
        -F data_type="gpx" \
        -F file=@/Users/nimiq/Desktop/1/cycling_2016-07-14_18-37-56.gpx | jq
    
    Response:
        {
            "id": 9482661447,
            "id_str": "9482661447",
            "external_id": null,
            "error": null,
            "status": "Your activity is still being processed.",
            "activity_id": null
        }
    
    Docs:
        - Authentication: https://developers.strava.com/docs/authentication/
        - API: https://developers.strava.com/docs/reference/#api-Uploads-createUpload
        - Upload activity: https://developers.strava.com/docs/uploads/
    """
    print(f"\nUploading {gpx_file_path}...")
    url = "https://www.strava.com/api/v3/uploads"
    payload = get_payload_for_gpx_file_name(gpx_file_path.name)
    headers = {"Authorization": f"Bearer {bearer_token}"}
    with open(gpx_file_path, "rb") as open_file:
        files = {"file": open_file}
        response = requests.post(url, files=files, data=payload, headers=headers)
    response.raise_for_status()
    print(
        response.json()
    )  # {'id': 9482993202, 'id_str': '9482993202', 'external_id': None, 'error': None, 'status': 'Your activity is still being processed.', 'activity_id': None}
    if not response.json().get("id"):
        raise Exception("Missing 'id' field in JSON response")


if __name__ == "__main__":
    print("START")
    main()
    print("END")
