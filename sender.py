import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from airtable import Airtable
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Airtable configuration
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

# Email configuration
SMTP_SERVER = os.environ["SMTP_SERVER"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
SMTP_PORT = 465  # Hardcoded for SSL

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent email to {to_email}")

def main():
    print("🚀 Starting email sender...")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        missing = [k for k in ["name", "company name", "email", "email 1"] if not fields.get(k)]

        if missing:
            print(f"⏭️ Skipping record — missing fields: {', '.join(missing)}")
            continue

        if fields.get("status"):
            print(f"⏭️ Skipping {fields['name']} — already marked as sent")
            continue

        try:
            print(f"📤 Sending to {fields['name']} ({fields['email']})")
            subject = f"Idea for {fields['company name']}"
            body = fields["email 1"]
            send_email(fields["email"], subject, body)

            now = datetime.now(LAGOS)
            airtable.update(record["id"], {
                "initial date": now.isoformat(),
                "follow-up 1 date": (now + timedelta(days=3)).isoformat(),
                "follow-up 2 date": (now + timedelta(days=7)).isoformat(),
                "status": "Sent"
            })
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed to send to {fields['email']}: {e}")

if __name__ == "__main__":
    main()
