import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Email setup
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# IMAP setup
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))

# --- Reply Detection ---
def check_replies():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, '(UNSEEN FROM "*")')
    if result != "OK":
        return []

    msg_ids = data[0].split()
    replied = set()

    for msg_id in msg_ids:
        result, msg_data = mail.fetch(msg_id, "(RFC822)")
        if result != "OK":
            continue
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        from_addr = email.utils.parseaddr(msg.get("From"))[1]
        if from_addr:
            replied.add(from_addr.lower())

    mail.logout()
    return list(replied)

# --- Send Email ---
def send_email(to_address, subject, body):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_address

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Get Leads to Send ---
def get_initial_leads():
    leads = airtable.get_all(view="Grid view")
    ready = []

    for lead in leads:
        fields = lead.get("fields", {})
        if not all(k in fields for k in ["name", "company name", "email", "website", "web copy"]):
            continue
        if fields.get("status", "").lower() == "replied":
            continue
        if "initial date" not in fields:
            ready.append(lead)

    return ready

# --- Main Run ---
def main():
    print("📬 Initial sender starting...")

    # 1. Detect replies
    replied = check_replies()
    for addr in replied:
        records = airtable.search("email", addr)
        for record in records:
            airtable.update(record["id"], {"status": "Replied"})
            print(f"✅ Marked {addr} as Replied")

    # 2. Send initial emails
    leads = get_initial_leads()
    for lead in leads:
        fields = lead["fields"]
        to_email = fields["email"]
        name = fields["name"]
        company = fields["company name"]

        subject = f"Quick idea for {company}"
        body = f"Hi {name},\n\n(Your email content here...)\n\nBest,\nToon Theory"

        try:
            send_email(to_email, subject, body)
            now = datetime.now().strftime("%Y-%m-%d")
            airtable.update(lead["id"], {
                "initial date": now,
                "status": "Sent"
            })
            print(f"📤 Sent to {to_email}")
        except Exception as e:
            print(f"❌ Error sending to {to_email}: {e}")

if __name__ == "__main__":
    main()
