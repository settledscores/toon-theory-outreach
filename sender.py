import os
import requests
from datetime import datetime
from airtable import Airtable
from dotenv import load_dotenv
import pytz

# Load .env variables
load_dotenv()

# Config
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
ZOHO_CLIENT_ID = os.environ['ZOHO_CLIENT_ID']
ZOHO_CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ZOHO_REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
ZOHO_ACCOUNT_ID = os.environ['ZOHO_ACCOUNT_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']

LAGOS = pytz.timezone('Africa/Lagos')

def refresh_access_token():
    url = 'https://accounts.zoho.com/oauth/v2/token'
    params = {
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, params=params)
    data = response.json()

    if 'access_token' not in data:
        print("❌ Failed to get token:", data)
        raise RuntimeError("Zoho token error")
    return data['access_token']

def send_email(access_token, to_email, subject, body):
    url = f'https://mail.zoho.com/api/accounts/{ZOHO_ACCOUNT_ID}/messages'
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'fromAddress': FROM_EMAIL,
        'toAddress': to_email,
        'subject': subject,
        'content': body,
        'mailFormat': 'plain',
        'saveToSent': True
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"❌ Zoho error ({response.status_code}): {response.text}")
        response.raise_for_status()

    print(f"✅ Sent email to {to_email}")
    return response.json()

def main():
    print("🚀 Starting email sender...")
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    access_token = refresh_access_token()
    sent_count = 0

    for record in records:
        fields = record.get("fields", {})
        if sent_count >= 3:
            break

        required = ['name', 'company name', 'email', 'email_1']
        if not all(k in fields and fields[k].strip() for k in required):
            continue

        if 'initial date' in fields:
            continue

        try:
            print(f"📤 Sending to {fields['name']} ({fields['email']} )")
            subject = f"Idea for {fields['company name']}"
            body = fields['email_1']
            send_email(access_token, fields['email'], subject, body)

            now = datetime.now(LAGOS)
            print(f"📝 Updating Airtable record: {record['id']}")
            payload = {
                'initial date': now.isoformat()
            }
            print("➡️ Payload:", payload)
            airtable.update(record['id'], payload)

            sent_count += 1

        except Exception as e:
            print(f"❌ Failed for {fields['email']}: {e}")

if __name__ == "__main__":
    main()
