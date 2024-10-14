import os
import requests


def get_published_file_details(id):
    workshop_api_url = (
        "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    )
    params = {
        "access_token": os.getenv("STEAM_ACCESS_TOKEN"),
        "itemcount": "1",
        "publishedfileids[0]": id,
    }

    r = requests.post(workshop_api_url, data=params)

    # TODO: Do response check

    sharedfile = r.json()["response"]["publishedfiledetails"][0]

    return sharedfile
