import os
import smtplib
import random
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime
import requests
from dotenv import load_dotenv
import pytz

load_dotenv()

NOCODB_API_KEY = os.getenv("NOCODB_API_KEY")
NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL")
PROJECT_ID = os.getenv("NOCODB_PROJECT_ID")
TABLE_ID = os.getenv("NOCODB_OUTREACH_TABLE_ID")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

LAGOS = pytz.timezone("Africa/Lagos")

API_BASE = f"{NOCODB_BASE_URL}/api/v1/projects/{PROJECT_ID}/tables/{TABLE_ID}/rows"
HEADERS = {
    "xc-auth": NOCODB_API_KEY,
    "Content-Type": "application/json"
}

SUBJECT_LINES = [
    "Let’s make your message stick", "Helping your story land", "Your idea → a great first impression",
    "A quick thought for your next launch", "Something different for {company}", 
    "Helping explain what {company} does — visually", "Here’s a fun idea worth testing", 
    "Your pitch deserves better than plain text", "Cut through the clutter", 
    "Explainers that make people pay attention", "Let's make your message unforgettable",
    "Got a moment, {name}?", "This might help simplify your message", "Show, don’t just tell",
    "Explainers that engage in 90 seconds", "Visual stories → higher conversions", 
    "Here’s a visual treatment idea", "Making complex → simple",
    "Stand out with animated storytelling", "This pitch idea works wonders",
    "People skim. Let’s grab their eyes.", "Need to simplify your pitch?", 
    "Making your story stick — fast", "3 ideas for {company}", 
    "Could animated content help your outreach?", "Animations that boost sales",
    "Ever tried this in your messaging?", "Turn your message into a scroll-stopper"
]

def fetch_records():
    res = requests.get(API_BASE, headers=HEADERS)
    res.raise_for_status()
    return res.json()["list"]

def update_record(record_id, payload):
    res = requests.patch(f"{API_BASE}/{record_id}", headers=HEADERS, json=payload)
    res.raise_for_status()

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Message-ID"] = make_msgid(domain=FROM_EMAIL.split("@")[-1])

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    return msg["Message-ID"].strip("<>")

def main():
    print("🚀 Sending initial emails via NocoDB...")
    used_subjects = set()
    records = fetch_records()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        name = record.get("name", "")
        company = record.get("company name", "")
        email_to = record.get("email", "")
        email1 = record.get("email 1", "")
        status = record.get("initial status", "")

        if not all([name, company, email_to, email1]) or status:
            continue

        try:
            subject_template = random.choice([s for s in SUBJECT_LINES if s not in used_subjects])
            used_subjects.add(subject_template)
            subject = subject_template.format(name=name, company=company)

            print(f"📤 Sending to {name} ({email_to})")
            message_id = send_email(email_to, subject, email1)
            now = datetime.now(LAGOS).isoformat()

            update_record(record["id"], {
                "initial date": now,
                "initial status": "Sent",
                "message id": message_id
            })

            print(f"✅ Email sent and logged for {name}")
            sent_count += 1
        except Exception as e:
            print(f"❌ Failed for {email_to}: {e}")
            now = datetime.now(LAGOS).isoformat()
            try:
                update_record(record["id"], {
                    "initial date": now,
                    "initial status": "Failed"
                })
            except Exception as err:
                print(f"⚠️ Failed to log error: {err}")

if __name__ == "__main__":
    main()
