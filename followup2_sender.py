# followup2_sender_test.py
import os
import smtplib
import random
import imaplib
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime
from airtable import Airtable
from dotenv import load_dotenv
import pytz
import time

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

# Subject lines for Follow-up 2 (25 variants)
SUBJECT_LINES = [
    "Any thoughts on this, {name}?", "Checking back in, {name}", "Quick follow-up, {name}",
    "Still curious if this helps", "Wondering if this sparked anything", "Visual storytelling, still on the table?",
    "A quick nudge your way", "Happy to mock something up", "Short reminder, {name}",
    "Just revisiting this idea", "Whiteboard sketch still an option?", "No pressure, just following up",
    "Back with another nudge", "A final nudge, {name}", "Hoping this reached you",
    "Revisiting that animation idea", "Let me know if now's better", "Still worth exploring?",
    "Quick question on our last email", "Still around if helpful", "Do you want me to close this out?",
    "Open to creative pitches?", "Visual ideas always on hand", "Just in case it got buried",
    "Hope this isn’t too forward"
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
            time.sleep(wait)

    message_id_3 = make_msgid()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to
    msg["Message-ID"] = message_id_3

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 2 to {to_email}")
    last_sent_time = datetime.now()
    return message_id_3.strip("<>")

def main():
    print("🚀 Follow-up 2 Sender Test Mode (weekend + 5min interval)")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        required = ["name", "company name", "email", "email 3", "follow-up 1 date", "message id 2"]
        if any(not fields.get(k) for k in required):
            continue

        if fields.get("follow-up 2 status"):
            continue

        if fields.get("reply") in ["after follow-up 1", "after follow-up 2"]:
            print(f"⛔ Skipping {fields['name']} — reply already received")
            continue

        if replied_to_message_id(fields["message id 2"]):
            airtable.update(record["id"], {"reply": "after follow-up 1"})
            print(f"📩 Reply detected for {fields['name']}. Skipping.")
            continue

        subject = random.choice(SUBJECT_LINES).format(
            name=fields["name"],
            company=fields["company name"]
        )
        to_email = fields["email"]
        body = fields["email 3"]
        in_reply_to = fields["message id 2"]

        msg_id_3 = send_threaded_email(to_email, subject, body, in_reply_to)

        now = datetime.now(LAGOS)
        airtable.update(record["id"], {
            "follow-up 2 date": now.isoformat(),
            "follow-up 2 status": "Sent",
            "message id 3": msg_id_3
        })
        sent_count += 1

if __name__ == "__main__":
    main()
