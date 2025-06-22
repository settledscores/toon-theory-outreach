# followup1_sender_test.py
import os
import smtplib
import random
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime, timedelta
from airtable import Airtable
from dotenv import load_dotenv
import pytz
import imaplib
import email

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
SMTP_PORT = 465
IMAP_SERVER = os.environ["IMAP_SERVER"]

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")

SUBJECT_LINES = [
    "just checking in, {name}", "thought I’d follow up, {name}", "quick ping, {name}",
    "any thoughts on this, {name}?", "circling back, {name}", "still thinking of {company}",
    "sketching some ideas for {company}", "a quick follow-up, {name}", "pinging you again, {name}",
    "any interest on this?", "here’s that idea again, {name}", "worth a peek, {name}?",
    "still open to this, {name}?", "quick check-in, {name}", "follow-up on that idea for {company}",
    "creative idea for {company}", "simple explainer?", "visualising {company}'s message",
    "nudging this up your inbox, {name}", "animation for {company}?",
    "missed this last time?", "revisiting an idea for {company}",
    "still thinking of that animation sketch", "starting visual ideas for {company}",
    "{name}, got a sec?", "where we left off, {name}", "circling back to that visual idea",
    "quick one for {company}", "a thought worth sharing", "follow-up from Toon Theory"
]

last_sent_time = None

def replied_to_message_id(message_id):
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
            imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            imap.select("INBOX")
            result, data = imap.search(None, f'HEADER In-Reply-To "{message_id}"')
            return bool(data[0].split())
    except Exception as e:
        print(f"⚠️ IMAP check failed: {e}")
        return False

def send_threaded_email(to_email, subject, body, in_reply_to):
    global last_sent_time
    if last_sent_time:
        diff = (datetime.now() - last_sent_time).total_seconds()
        if diff < 300:
            wait = 300 - diff
            print(f"⏳ Waiting {int(wait)}s before next send...")
            import time
            time.sleep(wait)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 1 to {to_email}")
    last_sent_time = datetime.now()

def main():
    print("🚀 Follow-up 1 Sender Test Mode (weekend + 5min interval)")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        required = ["name", "company name", "email", "email 2", "initial date", "message id"]
        if any(not fields.get(k) for k in required):
            continue

        if fields.get("follow-up 1 status"):
            continue

        if fields.get("reply") in ["after initial", "after follow-up 1", "after follow-up 2"]:
            print(f"⛔ Skipping {fields['name']} — reply already received")
            continue

        if replied_to_message_id(fields["message id"]):
            airtable.update(record["id"], {"reply": "after initial"})
            print(f"📩 Reply detected for {fields['name']}. Skipping.")
            continue

        subject = random.choice(SUBJECT_LINES).format(name=fields["name"], company=fields["company name"])
        send_threaded_email(fields["email"], subject, fields["email 2"], fields["message id"])

        now = datetime.now(LAGOS)
        airtable.update(record["id"], {
            "follow-up 1 date": now.isoformat(),
            "follow-up 1 status": "Sent"
        })
        sent_count += 1

if __name__ == "__main__":
    main()
