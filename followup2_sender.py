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

# Load environment variables
load_dotenv()

# Airtable config
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Email config
SMTP_SERVER = os.environ["SMTP_SERVER"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
SMTP_PORT = 465  # SSL

# Timezone
LAGOS = pytz.timezone("Africa/Lagos")

# Weekday-safe scheduling
def is_safe_weekday(dt):
    weekday = dt.weekday()
    return weekday not in [4, 5, 6]  # 4=Friday, 5=Saturday, 6=Sunday

def find_next_safe_day(base_date, offset_days):
    next_date = base_date + timedelta(days=offset_days)
    while not is_safe_weekday(next_date):
        next_date += timedelta(days=1)
    return next_date

# Rotating subject lines
SUBJECT_LINES = [
    "Just circling back, {name}",
    "Following up quickly, {name}",
    "Still up for a creative idea, {name}?",
    "Checking in from Toon Theory, {name}",
    "Wondering your thoughts, {name}",
    "Wanted to loop back on this",
    "Are you open to this idea?",
    "We can show it, not just tell it",
    "Still curious if you’re exploring visuals?",
    "One last idea to try",
    "Animation could bring this to life",
    "Still on the table if you're curious",
    "A gentle nudge, {name}",
    "You might like this one, {name}",
    "Hope your week's going well, {name}",
    "Here’s that visual idea again",
    "Still happy to sketch something up",
    "How’s this for timing, {name}?",
    "Just checking back in here",
    "Worth one more shot?",
    "Still worth exploring this?",
    "This could help {company}",
    "Let’s bring one idea to life visually",
    "Circling back with a thought",
    "Have a second to revisit this?"
]

def send_email(to_email, subject, body, in_reply_to=None):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    msg_id = make_msgid(domain="toontheory.com")
    msg["Message-ID"] = msg_id

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

    print(f"✅ Sent follow-up 2 to {to_email}")
    return msg_id.strip("<>")

def main():
    print("🚀 Starting follow-up 2 sender...")

    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    sent_count = 0

    for record in records:
        if sent_count >= 3:
            break

        fields = record.get("fields", {})
        required = ["name", "email", "company name", "email 3", "follow-up 1 date", "follow-up 1 status", "message id 2"]
        if not all(fields.get(k) for k in required):
            continue

        if fields.get("follow-up 2 status"):
            print(f"⏭️ Skipping {fields['name']} — already marked as sent or failed for follow-up 2")
            continue

        try:
            # Parse previous date
            f1_date = datetime.fromisoformat(fields["follow-up 1 date"])
            f1_date = f1_date.astimezone(LAGOS)

            # Determine next weekday-safe follow-up date (typically +3 days)
            target_date = find_next_safe_day(f1_date, 3)
            now = datetime.now(LAGOS)

            # Wait until target date
            if now.date() < target_date.date():
                continue

            # Email prep
            subject = random.choice(SUBJECT_LINES).format(
                name=fields["name"],
                company=fields["company name"]
            )
            body = fields["email 3"]
            reply_to_id = fields["message id 2"]

            # Send email
            msg_id = send_email(fields["email"], subject, body, in_reply_to=reply_to_id)

            # Update Airtable
            now_str = now.isoformat()
            airtable.update(record["id"], {
                "follow-up 2 date": now_str,
                "follow-up 2 status": "Sent",
                "message id 3": msg_id
            })

            sent_count += 1
            print(f"📝 Airtable updated for: {fields['name']}")

        except Exception as e:
            print(f"❌ Error for {fields.get('email')}: {e}")
            try:
                airtable.update(record["id"], {
                    "follow-up 2 date": datetime.now(LAGOS).isoformat(),
                    "follow-up 2 status": "Failed"
                })
                print(f"⚠️ Logged failure for {fields['name']}")
            except Exception as update_error:
                print(f"❌ Airtable update failed after error: {update_error}")

    print(f"\n🎯 Done. {sent_count} follow-up 2 emails sent.")

if __name__ == "__main__":
    main()
