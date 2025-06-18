import os
import requests
from datetime import datetime, timedelta
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
ZOHO_CLIENT_ID = os.environ['ZOHO_CLIENT_ID']
ZOHO_CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ZOHO_REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
ZOHO_ACCOUNT_ID = os.environ['ZOHO_ACCOUNT_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']

def refresh_access_token():
    url = 'https://accounts.zoho.com/oauth/v2/token'
    params = {
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, params=params)
    
    try:
        data = response.json()
    except Exception:
        raise RuntimeError(f"❌ Non-JSON response: {response.text}")

    if 'access_token' not in data:
        print("🔎 Debug response from Zoho:", data)
        raise RuntimeError(f"❌ Could not refresh token: {data}")
    
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
        'mailFormat': 'plain'
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def main():
    print("🔐 Loaded refresh token:", ZOHO_REFRESH_TOKEN[:8] + "..." if ZOHO_REFRESH_TOKEN else "Not found")
    
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    access_token = refresh_access_token()
    sent_count = 0

    for record in records:
        fields = record.get("fields", {})
        if sent_count >= 3:
            break

        required = ['name', 'company name', 'email', 'email 1']
        if not all(k in fields and fields[k].strip() for k in required):
            continue

        if fields.get("status"):  # Already sent or handled
            continue

        try:
            print(f"📤 Sending to {fields['name']} ({fields['email']})")
            subject = f"Idea for {fields['company name']}"
            body = fields['email 1']
            send_email(access_token, fields['email'], subject, body)

            now = datetime.utcnow()
            airtable.update(record['id'], {
                'initial date': now.isoformat(),
                'follow-up 1 date': (now + timedelta(days=3)).isoformat(),
                'follow-up 2 date': (now + timedelta(days=7)).isoformat(),
                'status': 'Sent'
            })
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed to send to {fields['email']}: {e}")

if __name__ == "__main__":
    print("🚀 Starting email sender...")
    main()
