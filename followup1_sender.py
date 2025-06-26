import os
import smtplib
import random
import imaplib
import email
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime, timedelta
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

# Subject line variations (capitalized and fixed)
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

last_sent_time = None

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

    message_id_2 = make_msgid()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to
    msg["Message-ID"] = message_id_2

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 1 to {to_email}")
    last_sent_time = datetime.now()
    return message_id_2.strip("<>")

def main():
    print("🚀 Follow-up 1 Sender (reply-aware + 5min intervals)")

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

        reply_state = fields.get("reply", "").lower()
        if reply_state in ["after initial", "after follow-up 1", "after follow-up 2"]:
            print(f"⛔ Skipping {fields['name']} — reply state: {reply_state}")
            continue

        if replied_to_message_id(fields["message id"], fields["email"]):
            airtable.update(record["id"], {"reply": "after initial"})
            print(f"📩 Reply detected for {fields['name']}. Skipping.")
            continue

        subject = random.choice(SUBJECT_LINES).format(
            name=fields["name"],
            company=fields["company name"]
        )
        to_email = fields["email"]
        body = fields["email 2"]
        in_reply_to = fields["message id"]

        msg_id_2 = send_threaded_email(to_email, subject, body, in_reply_to)

        now = datetime.now(LAGOS)
        airtable.update(record["id"], {
            "follow-up 1 date": now.isoformat(),
            "follow-up 1 status": "Sent",
            "message id 2": msg_id_2
        })
        sent_count += 1

if __name__ == "__main__":
    main()
