import os
import requests
import time
from datetime import datetime, timedelta
from airtable import Airtable
from dotenv import load_dotenv
from email.utils import formataddr

load_dotenv()

# === Constants ===
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
ZOHO_CLIENT_ID = os.environ['ZOHO_CLIENT_ID']
ZOHO_CLIENT_SECRET = os.environ['ZOHO_CLIENT_SECRET']
ZOHO_REFRESH_TOKEN = os.environ['ZOHO_REFRESH_TOKEN']
ZOHO_ACCOUNT_ID = os.environ['ZOHO_ACCOUNT_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']

PROMPT_TEMPLATE = """You're helping a whiteboard animation studio write a cold outreach email.

Here is their base email:

Hi {name},

I’ve been following {company} lately, and your ability to make {summary} really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on {angle}, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

- [Use case #1 tailored to website content]
- [Use case #2 tailored to website content]
- [Use case #3 tailored to website content]

If you're open to it, I’d love to draft a sample script or sketch out a short ten-second demo to demonstrate one of these use cases, all at no cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.

[Dynamic closer based on brand tone or mission. For example: “Thanks for making data feel human, it’s genuinely refreshing.” Or “Thanks for making healthcare more accessible, it's inspiring.”]

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content: {web_copy}
"""

# === Access token refresher ===
def refresh_access_token():
    response = requests.post(
        'https://accounts.zoho.com/oauth/v2/token',
        params={
            'refresh_token': ZOHO_REFRESH_TOKEN,
            'client_id': ZOHO_CLIENT_ID,
            'client_secret': ZOHO_CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
    )
    response.raise_for_status()
    return response.json()['access_token']

# === Compose email from prompt ===
def generate_email(name, company, web_copy):
    summary = "complex topics approachable"
    angle = "clarity and communication"
    return PROMPT_TEMPLATE.format(name=name, company=company, summary=summary, angle=angle, web_copy=web_copy)

# === Send email via Zoho ===
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

# === Main logic ===
def main():
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    access_token = refresh_access_token()
    sent_count = 0

    for record in records:
        fields = record['fields']
        if sent_count >= 3:
            break

        required_keys = ['name', 'company name', 'email', 'website', 'web copy']
        if not all(k in fields and fields[k].strip() for k in required_keys):
            continue

        email_body = generate_email(fields['name'], fields['company name'], fields['web copy'])
        try:
            print(f"📤 Sending to {fields['name']} ({fields['email']})")
            send_email(access_token, fields['email'], "Idea for {company}".format(company=fields['company name']), email_body)

            now = datetime.utcnow()
            airtable.update(record['id'], {
                'initial date': now.isoformat(),
                'follow-up 1 date': (now + timedelta(minutes=5)).isoformat(),
                'follow-up 2 date': (now + timedelta(minutes=10)).isoformat(),
                'status': 'Sent'
            })
            sent_count += 1
        except Exception as e:
            print(f"❌ Failed to send to {fields['email']}: {e}")

if __name__ == '__main__':
    print("🚀 Starting outreach script...")
    main()
