import os
import smtplib
import random
from email.mime.text import MIMEText
from datetime import datetime
from airtable import Airtable
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Airtable config
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

# Email config
SMTP_SERVER = os.environ["SMTP_SERVER"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
SMTP_PORT = 465  # SSL

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")

# Subject line rotation
SUBJECT_LINES = [
    "Let’s make your message stick",
    "A quick thought for your next project",
    "Helping your ideas stick visually",
    "Turn complex into simple (in 90 seconds)",
    "Your story deserves to be told differently",
    "How about a different approach to your messaging?",
    "Making your story unforgettable",
    "Bring your message to life — visually",
    "Your pitch deserves more than plain text",
    "What if your message spoke in pictures?",
    "Visual stories make better first impressions",
    "Helping businesses explain what makes them different",
    "Cut through noise with visual storytelling",
    "A visual idea for {company}",
    "Explainers that make people pay attention",
    "What if you could show it instead of tell it?",
    "Here’s a visual idea worth testing",
    "Explaining complex stuff with simple visuals",
    "Is your message reaching it's full potential?",
    "A story-first idea for {company}",
    "Cut through mess and set your message free",
    "Idea: use animation to make your message land",
    "This might help supercharge your next big project",
    "How do you explain what {company} does?",
    "Let’s make it click — visually"
]

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
        required = ["name", "company name", "email", "email 1"]
        missing = [k for k in required if not fields.get(k)]

        if missing:
            print(f"⏭️ Skipping record — missing fields: {', '.join(missing)}")
            continue

        if fields.get("initial status"):
            print(f"⏭️ Skipping {fields['name']} — already marked as sent or failed")
            continue

        try:
            company = fields["company name"]
            subject_template = random.choice(SUBJECT_LINES)
            subject = subject_template.format(company=company)
            body = fields["email 1"]

            print(f"📤 Sending to {fields['name']} ({fields['email']})")
            send_email(fields["email"], subject, body)

            now = datetime.now(LAGOS)
            update_payload = {
                "initial date": now.isoformat(),
                "initial status": "Sent"
            }

            airtable.update(record["id"], update_payload)
            print(f"✅ Airtable updated for: {fields['name']}")
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed for {fields.get('email')}: {e}")
            now = datetime.now(LAGOS)
            fail_payload = {
                "initial date": now.isoformat(),
                "initial status": "Failed"
            }
            try:
                airtable.update(record["id"], fail_payload)
                print(f"⚠️ Logged failure for {fields.get('name')}")
            except Exception as update_error:
                print(f"❌ Airtable update error after failure: {update_error}")

if __name__ == "__main__":
    main()
