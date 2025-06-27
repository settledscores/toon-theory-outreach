import os
import smtplib
import random
import imaplib
import email
import time
import requests
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime
from dotenv import load_dotenv
import pytz

load_dotenv()

# NocoDB config
NOCODB_API_KEY = os.getenv("NOCODB_API_KEY")
NOCODB_PROJECT_ID = os.getenv("NOCODB_PROJECT_ID")
NOCODB_OUTREACH_TABLE_ID = os.getenv("NOCODB_OUTREACH_TABLE_ID")
NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL")
API_BASE = f"{NOCODB_BASE_URL}/v1/db/data"

HEADERS = {"Authorization": f"Bearer {NOCODB_API_KEY}"}

# Email config
SMTP_SERVER = os.getenv("SMTP_SERVER")
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")
SMTP_PORT = 465

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")
last_sent_time = None

SUBJECT_LINES = [
    "Just Checking In, {name}",
    "Thought I’d Follow Up, {name}",
    "Any Thoughts On This, {name}?",
    "Circling Back, {name}",
    "Sketching Some Ideas For {company}",
    "A Quick Follow-Up, {name}",
    "Any Interest In This, {name}?",
    "Here’s That Idea Again, {name}",
    "Are You Still Open To This, {name}?",
    "Quick Check-In, {name}",
    "Following Up On That Idea For {company}",
    "Nudging This Up Your Inbox, {name}",
    "Revisiting, Just In Case You Missed This The Last Time, {name}",
    "{name}, Got A Sec?",
    "Circling Back To That Idea For {company}",
    "A Follow-Up From Toon Theory, {name}"
]

def fetch_records():
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()["list"]

def update_record(record_id, updates):
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows/{record_id}"
    r = requests.patch(url, headers={**HEADERS, "Content-Type": "application/json"}, json=updates)
    r.raise_for_status()

def replied_to_message_id(message_id, sender_email):
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
            imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            imap.select("INBOX")
            search_criteria = f'(FROM "{sender_email}" (OR HEADER In-Reply-To "{message_id}" HEADER References "{message_id}"))'
            result, data = imap.search(None, search_criteria)
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
            time.sleep(wait)

    msg_id = make_msgid()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to
    msg["Message-ID"] = msg_id

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 1 to {to_email}")
    last_sent_time = datetime.now()
    return msg_id.strip("<>")

def main():
    print("🚀 Follow-up 1 Sender (reply-aware + 5min pacing)")
    records = fetch_records()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        f = record
        required = ["name", "company name", "email", "email 2", "initial date", "message id"]
        if any(not f.get(k) for k in required):
            continue

        if f.get("follow-up 1 status"):
            continue

        reply_flag = str(f.get("reply", "")).lower()
        if reply_flag in ["after initial", "after follow-up 1", "after follow-up 2"]:
            continue

        if replied_to_message_id(f["message id"], f["email"]):
            update_record(f["id"], {"reply": "after initial"})
            continue

        subject = random.choice(SUBJECT_LINES).format(name=f["name"], company=f["company name"])
        msg_id_2 = send_threaded_email(f["email"], subject, f["email 2"], f["message id"])
        now = datetime.now(LAGOS).isoformat()

        update_record(f["id"], {
            "follow-up 1 date": now,
            "follow-up 1 status": "Sent",
            "message id 2": msg_id_2
        })
        sent_count += 1

if __name__ == "__main__":
    main()
