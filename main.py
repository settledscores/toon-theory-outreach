import os
import random
import smtplib
import imaplib
import email
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
from airtable import Airtable

# === Setup ===
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # optional fallback if using Groq
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

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

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content: {web_copy}
"""

def generate_email(name, company, web_copy):
    prompt = PROMPT_TEMPLATE.format(
        name=name,
        company=company,
        summary="complex ideas feel simple and actionable",
        angle="clarity and storytelling",
        web_copy=web_copy,
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior B2B copywriter."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

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

def should_send_today(date_str):
    if not date_str:
        return True
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return date.date() <= datetime.now().date()

def main():
    print("🚀 Starting cold outreach script...\n")

    records = airtable.get_all()
    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        to_email = fields.get("email", "").strip()
        web_copy = fields.get("web copy", "").strip()
        status = fields.get("status", "").strip().lower()
        initial_date = fields.get("initial date", "")

        print(f"🔍 Reviewing: {name} | {company} | {to_email} | Status: {status or 'N/A'}")

        if not all([name, company, to_email, web_copy]):
            print("❌ Skipped: Missing required fields.\n")
            continue

        if status not in ("", "not contacted") or not should_send_today(initial_date):
            print("⏩ Skipped: Already contacted or not scheduled.\n")
            continue

        print(f"✅ Preparing email for {name} at {company} ({to_email})...")
        try:
            email_body = generate_email(name, company, web_copy)
            send_email(to_email, f"Quick idea for {company}", email_body)

            today_str = datetime.now().strftime("%Y-%m-%d")
            airtable.update(record["id"], {
                "initial date": today_str,
                "follow-up 1 date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "follow-up 2 date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "status": "sent"
            })
            print("📬 Email sent and Airtable updated.\n")
        except Exception as e:
            print(f"❗ Error sending to {to_email}: {e}\n")

if __name__ == "__main__":
    main()
