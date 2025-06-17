import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from airtable import Airtable
from datetime import datetime, timedelta
import random
import time
import openai

# === Environment ===
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# === Prompt template ===
PROMPT_TEMPLATE = """You're helping a whiteboard animation studio write a cold outreach email.

Here is their base email:

Hi {name},

I’ve been following {company} lately, and your ability to make {summary} really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on {angle}, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to: 

- [Use case #1 tailored to website content]
- [Use case #2 tailored to website content]
- [Use case #3 tailored to website content]

If you're open to it, I’d love to draft a sample script or sketch out a short ten-second demo to demonstrate one of these use cases, all at no cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.

[Dynamic closer based on brand tone or mission. For example: “Thanks for making data feel human, it’s genuinely refreshing.” Or “Thanks for making healthcare more accessible, it's inspiring.”]

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust

Based on the website content below, fill in the missing parts in the email with clear, natural language.

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content: {web_copy}
"""

# === Airtable Setup ===
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# === Generate email ===
def generate_email(name, company, web_copy):
    prompt = PROMPT_TEMPLATE.format(name=name, company=company, summary="", angle="", web_copy=web_copy)
    openai.api_key = GROQ_API_KEY
    response = openai.ChatCompletion.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# === Send email ===
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# === Check inbox for replies ===
def check_replies():
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, '(UNSEEN)')
        unread_msg_nums = data[0].split()

        for num in unread_msg_nums:
            result, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            from_email = email.utils.parseaddr(msg["From"])[1]

            # Update Airtable status to "replied"
            matching = airtable.search("email", from_email)
            for match in matching:
                airtable.update(match["id"], {"status": "replied"})
                print(f"📩 Reply received from {from_email} — marked as replied.")

# === Main ===
def main():
    print("🚀 Starting cold outreach script...\n")
    check_replies()

    records = airtable.get_all()
    eligible = []

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name")
        company = fields.get("company name")
        email_addr = fields.get("email")
        website = fields.get("website")
        web_copy = fields.get("web copy")
        status = fields.get("status", "").lower()

        log_parts = []
        if not name:
            log_parts.append("missing name")
        if not company:
            log_parts.append("missing company name")
        if not email_addr:
            log_parts.append("missing email")
        if not website:
            log_parts.append("missing website")
        if not web_copy:
            log_parts.append("missing web copy")
        if status.startswith("sent") or status == "replied":
            log_parts.append(f"status is '{status}'")

        if log_parts:
            print(f"⛔ Skipping lead: {email_addr or '[no email]'} — " + ", ".join(log_parts))
        else:
            eligible.append((record["id"], name, company, email_addr, web_copy))

    if not eligible:
        print("❌ No eligible leads found.")
        return

    # Pick one lead to send to
    lead_id, name, company, email_addr, web_copy = random.choice(eligible)
    print(f"✅ Preparing email for {name} at {company} ({email_addr})...")

    email_body = generate_email(name, company, web_copy)
    send_email(email_addr, f"Quick idea for {company}", email_body)

    now = datetime.utcnow()
    airtable.update(lead_id, {
        "status": "sent initial",
        "initial date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "follow-up 1 date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "follow-up 2 date": (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
    })
    print(f"✅ Email sent and Airtable updated for {email_addr}.")

if __name__ == "__main__":
    main()
