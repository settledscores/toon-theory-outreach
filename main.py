import os
import smtplib
import imaplib
import email
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from airtable import Airtable
from openai import OpenAI
from dotenv import load_dotenv
import random
import time

# === Load environment variables ===
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))

# === Airtable setup ===
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, api_key=AIRTABLE_API_KEY)

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

# === Helper functions ===
def generate_email_prompt(name, company, web_copy):
    return PROMPT_TEMPLATE.format(name=name, company=company, web_copy=web_copy, summary="{summary}", angle="{angle}")

def call_groq(prompt):
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def send_email(recipient, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def check_reply(recipient_email):
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, f'FROM "{recipient_email}"')
        if status == "OK" and messages[0]:
            return True
    return False

def get_eligible_leads():
    records = airtable.get_all()
    eligible = []
    for record in records:
        f = record["fields"]
        if all(k in f and f[k] for k in ["name", "company name", "email", "website", "web copy"]):
            status = f.get("status", "").lower()
            if not status.startswith("sent"):
                eligible.append(record)
    return eligible

def update_follow_up_dates(record_id, initial_time):
    follow_up_1 = initial_time + timedelta(days=3)
    follow_up_2 = follow_up_1 + timedelta(days=4)
    airtable.update(record_id, {
        "initial date": initial_time.isoformat(),
        "follow-up 1 date": follow_up_1.isoformat(),
        "follow-up 2 date": follow_up_2.isoformat(),
        "status": "sent initial"
    })

# === Main function ===
def main():
    leads = get_eligible_leads()
    if not leads:
        print("❌ No eligible leads found.")
        return

    lead = random.choice(leads)
    f = lead["fields"]
    record_id = lead["id"]
    name = f["name"]
    company = f["company name"]
    recipient = f["email"]
    web_copy = f["web copy"]

    print(f"🟡 Preparing email for {name} at {company} ({recipient})")

    prompt = generate_email_prompt(name, company, web_copy)
    email_body = call_groq(prompt)

    subject = f"Quick idea for {company}"

    send_email(recipient, subject, email_body)
    now = datetime.now()
    update_follow_up_dates(record_id, now)

    print(f"✅ Email sent to {name} at {company} at {now.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
