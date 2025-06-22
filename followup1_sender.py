import os
import smtplib
import random
from email.mime.text import MIMEText
from email.utils import make_msgid
from datetime import datetime, timedelta
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

# Subject line rotation (30 variants)
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

def get_next_valid_date(start_date):
    next_date = start_date + timedelta(days=1)
    while next_date.weekday() in [4, 5, 6]:  # Skip Fri, Sat, Sun
        next_date += timedelta(days=1)
    return next_date

def calculate_followup_date(initial_iso):
    initial_date = datetime.fromisoformat(initial_iso)
    count = 0
    next_date = initial_date
    while count < 3:
        next_date += timedelta(days=1)
        if next_date.weekday() < 4:  # Mon-Thu only
            count += 1
    return next_date

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

    print(f"✅ Sent follow-up 1 to {to_email}")

def main():
    print("🚀 Starting Follow-up 1 sender...")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        required = ["name", "company name", "email", "email 2", "initial date", "message id"]
        missing = [k for k in required if not fields.get(k)]

        if missing:
            print(f"⏭️ Skipping — missing fields: {', '.join(missing)}")
            continue

        if fields.get("follow-up 1 status"):
            print(f"⏭️ Skipping {fields['name']} — already sent follow-up 1")
            continue

        try:
            initial_iso = fields["initial date"]
            target_date = calculate_followup_date(initial_iso)
            now = datetime.now(LAGOS)

            if now.date() != target_date.date():
                print(f"🕒 Not time yet for {fields['name']} — waiting until {target_date.date()}")
                continue

            name = fields["name"]
            company = fields["company name"]
            subject = random.choice(SUBJECT_LINES).format(name=name, company=company)
            body = fields["email 2"]
            to_email = fields["email"]
            message_id = fields["message id"]

            send_threaded_email(to_email, subject, body, message_id)

            update_payload = {
                "follow-up 1 date": now.isoformat(),
                "follow-up 1 status": "Sent"
            }
            airtable.update(record["id"], update_payload)
            print(f"✅ Airtable updated for: {name}")
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed for {fields.get('email')}: {e}")
            try:
                airtable.update(record["id"], {"follow-up 1 status": "Failed"})
            except:
                pass

if __name__ == "__main__":
    main()
