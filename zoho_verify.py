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

def list_mail_accounts(token):
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    url = "https://mail.zoho.com/api/accounts"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to list accounts: {res.status_code} {res.text}")
        return None
    return res.json()

def list_folders(token, account_id):
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    url = f"https://mail.zoho.com/api/accounts/{account_id}/folders"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to list folders: {res.status_code} {res.text}")
        return None
    return res.json()

if __name__ == "__main__":
    token = get_access_token()
    print("Access token obtained.")

    accounts = list_mail_accounts(token)
    if accounts:
        print("Mail accounts:", accounts)
        account_id = accounts['data'][0]['accountId']
        print(f"Using account ID: {account_id}")

        folders = list_folders(token, account_id)
        if folders:
            print("Folders fetched successfully:")
            for folder in folders.get("data", []):
                print(f"- {folder['folderName']}")
        else:
            print("Could not fetch folders — check API access and permissions.")
    else:
        print("Could not list mail accounts — check API access and permissions.")
