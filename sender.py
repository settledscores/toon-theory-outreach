import os
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
from airtable import Airtable
from dotenv import load_dotenv
import pytz

# Load .env (optional, for local testing)
load_dotenv()

# Timezone
LAGOS = pytz.timezone('Africa/Lagos')

# Environment variables
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT_STR = os.getenv("SMTP_PORT")

if not SMTP_PORT_STR:
    raise RuntimeError("❌ SMTP_PORT is not set or is empty")

SMTP_PORT = int(SMTP_PORT_STR)

# Airtable setup
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        print(f"✅ Email sent to {to_email}")

def main():
    print("🚀 Starting email sender...")
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        fields = record.get("fields", {})
        required_fields = ['name', 'company name', 'email', 'email 1']

        if sent_count >= 3:
            break

        if not all(k in fields and fields[k].strip() for k in required_fields):
            continue

        if fields.get("status"):
            continue

        try:
            to_email = fields['email']
            subject = f"Idea for {fields['company name']}"
            body = fields['email 1']
            send_email(to_email, subject, body)

            now = datetime.now(LAGOS)
            airtable.update(record['id'], {
                'initial date': now.isoformat(),
                'status': 'Sent'
            })

            sent_count += 1

        except Exception as e:
            print(f"❌ Failed to send to {fields.get('email')}: {e}")

if __name__ == "__main__":
    main()
