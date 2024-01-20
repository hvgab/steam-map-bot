import os
import requests


def get_published_file_details(id):
    workshop_api_url = (
        "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    )
    params = {
        "access_token": os.getenv("steam_access_token"),
        "itemcount": "1",
        "publishedfileids[0]": id,
    }

    r = requests.post(workshop_api_url, data=params)

    # Do response check

    sharedfile = r.json()["response"]["publishedfiledetails"][0]

    return sharedfile


if __name__ == "__main__":
    pub = get_published_file_details(3108198185)
    print(pub)
