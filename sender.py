import os
import smtplib
import random
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime
from dotenv import load_dotenv
import pytz
import requests

load_dotenv()

# Config
BASEROW_API_KEY = os.getenv("BASEROW_API_KEY")
BASEROW_OUTREACH_TABLE = os.getenv("BASEROW_OUTREACH_TABLE")
BASE_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_OUTREACH_TABLE}"
HEADERS = {
    "Authorization": f"Token {BASEROW_API_KEY}",
    "Content-Type": "application/json"
}

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

LAGOS = pytz.timezone("Africa/Lagos")

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

def fetch_records():
    res = requests.get(BASE_URL + "?user_field_names=true", headers=HEADERS)
    res.raise_for_status()
    return res.json()["results"]

def update_record(record_id, payload):
    res = requests.patch(f"{BASE_URL}/{record_id}/", headers=HEADERS, json=payload)
    res.raise_for_status()

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    message_id = make_msgid(domain=FROM_EMAIL.split("@")[-1])
    msg["Message-ID"] = message_id

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    return message_id.strip("<>")

def main():
    print("🚀 Sending initial emails...")

    used_subjects = set()
    records = fetch_records()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record
        record_id = fields["id"]

        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        email_to = fields.get("email", "").strip()
        email1 = fields.get("email 1", "").strip()
        status = fields.get("initial status", "")

        if not all([name, company, email_to, email1]):
            print(f"⏭️ Skipping {record_id} — missing required fields")
            continue

        if status:
            print(f"⏭️ Skipping {name} — already marked as sent or failed")
            continue

        try:
            available_subjects = [s for s in SUBJECT_LINES if s not in used_subjects]
            if not available_subjects:
                used_subjects.clear()
                available_subjects = SUBJECT_LINES.copy()

            subject_template = random.choice(available_subjects)
            used_subjects.add(subject_template)
            subject = subject_template.format(company=company)

            print(f"📤 Sending to {name} ({email_to})")
            message_id = send_email(email_to, subject, email1)

            now = datetime.now(LAGOS).isoformat()
            update_payload = {
                "initial date": now,
                "initial status": "Sent",
                "message id": message_id
            }

            update_record(record_id, update_payload)
            print(f"✅ Updated Baserow for {name}")
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed for {email_to}: {e}")
            now = datetime.now(LAGOS).isoformat()
            fail_payload = {
                "initial date": now,
                "initial status": "Failed"
            }
            try:
                update_record(record_id, fail_payload)
                print(f"⚠️ Logged failure for {name}")
            except Exception as uerr:
                print(f"❌ Error updating failure: {uerr}")

if __name__ == "__main__":
    main()
