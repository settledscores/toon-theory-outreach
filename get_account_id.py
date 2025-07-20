import os
import requests

def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": os.environ["ZOHO_REFRESH_TOKEN"],
        "client_id": os.environ["ZOHO_CLIENT_ID"],
        "client_secret": os.environ["ZOHO_CLIENT_SECRET"],
        "grant_type": "refresh_token"
    }
    res = requests.post(url, params=params)
    res.raise_for_status()
    return res.json()["access_token"]

def get_account_id(token):
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    res = requests.get("https://mail.zoho.com/api/accounts", headers=headers)
    res.raise_for_status()
    data = res.json()["data"][0]
    print(f"✅ Zoho Account ID: {data['accountId']}")
    return data['accountId']

if __name__ == "__main__":
    token = get_access_token()
    account_id = get_account_id(token)
