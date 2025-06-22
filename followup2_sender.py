import os
import smtplib
import random
import time
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
IMAP_SERVER = os.environ["IMAP_SERVER"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
SMTP_PORT = 465  # SSL

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")

# Subject line rotation
SUBJECT_LINES = [
    "just following up, {name}", "quick check in, {name}", "pinging you again, {name}",
    "any thoughts on that idea?", "back with that animation thought", "quick idea for {company}",
    "sketching this again for {company}", "second thought, {name}", "visual idea, round 2",
    "didn’t want you to miss this", "this might still be useful", "let me know your thoughts",
    "worth another peek?", "wanted to loop back", "a visual reminder, {name}",
    "still thinking of {company}", "just one more sketch for you", "this could be a fit",
    "still here if you're curious", "picking up where we left off", "another visual nudge",
    "idea: simplify with a sketch", "animation still on the table?", "still up for a quick collab?",
    "this could bring clarity to {company}"
]

def fetch_replied_ids():
    replied_ids = set()
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        result, data = mail.search(None, 'UNSEEN')
        if result != "OK":
            return replied_ids

        for num in data[0].split():
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            in_reply_to = msg.get("In-Reply-To")
            if in_reply_to:
                replied_ids.add(in_reply_to.strip())
        mail.logout()
    except Exception as e:
        print(f"❌ IMAP error: {e}")
    return replied_ids

def send_threaded_email(to_email, subject, body, in_reply_to):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["In-Reply-To"] = in_reply_to
    msg["References"] = in_reply_to

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 2 to {to_email}")

def main():
    print("🚀 Starting Follow-up 2 sender...")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    replied_ids = fetch_replied_ids()

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        required = ["name", "company name", "email", "email 3", "follow-up 1 date", "message id 2"]
        missing = [k for k in required if not fields.get(k)]

        if missing:
            print(f"⏭️ Skipping — missing fields: {', '.join(missing)}")
            continue

        if fields.get("follow-up 2 status"):
            print(f"⏭️ Skipping {fields['name']} — already sent follow-up 2")
            continue

        msg_id_2 = fields["message id 2"].strip()
        if msg_id_2 in replied_ids:
            print(f"📭 Reply detected for {fields['name']} — skipping send and updating reply field.")
            airtable.update(record["id"], {"reply": "after follow-up 1"})
            continue

        try:
            subject = random.choice(SUBJECT_LINES).format(name=fields["name"], company=fields["company name"])
            body = fields["email 3"]
            to_email = fields["email"]
            in_reply_to = fields["message id 2"]

            send_threaded_email(to_email, subject, body, in_reply_to)

            now = datetime.now(LAGOS)
            update_payload = {
                "follow-up 2 date": now.isoformat(),
                "follow-up 2 status": "Sent"
            }
            airtable.update(record["id"], update_payload)
            print(f"✅ Airtable updated for: {fields['name']}")
            sent_count += 1

            if sent_count < 3:
                time.sleep(300)  # 5-minute interval

        except Exception as e:
            print(f"❌ Failed for {fields.get('email')}: {e}")
            try:
                airtable.update(record["id"], {"follow-up 2 status": "Failed"})
            except:
                pass

if __name__ == "__main__":
    main()
