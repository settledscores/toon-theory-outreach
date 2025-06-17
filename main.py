import os
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from airtable import Airtable
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Airtable Setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_VIEW_NAME = os.getenv("AIRTABLE_VIEW_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# OpenAI
openai = OpenAI(api_key=os.getenv("GROQ_API_KEY"))

# Email (Zoho SMTP)
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
SMTP_USERNAME = "hello@toontheory.com"
SMTP_PASSWORD = os.getenv("ZOHO_APP_PASSWORD")

# Google Sheets mode OFF — Airtable only
USE_AIRTABLE = True

# Timezone
TZ_OFFSET = timedelta(hours=1)  # WAT (UTC+1)

# Random delay range (secs)
DELAY_RANGE = (1, 5)

# Max emails per day
MAX_EMAILS_PER_DAY = 20


def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url.strip("/")
    return url.strip("/")


def scrape_visible_text(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "a"]):
            tag.decompose()

        return " ".join(soup.stripped_strings)
    except Exception as e:
        print(f"⚠️ Scraping failed for {url}: {e}")
        return ""


def is_valid_lead(record):
    required = ["name", "company name", "email", "website", "web copy"]
    missing = [field for field in required if not record.get("fields", {}).get(field)]
    return (len(missing) == 0, missing)


def generate_prompt(name, company, web_copy):
    return f"Write a short, friendly cold outreach email to {name} at {company} based on this web copy: {web_copy}"


def send_email(recipient, subject, body):
    msg = MIMEText(body)
    msg["From"] = SMTP_USERNAME
    msg["To"] = recipient
    msg["Subject"] = subject

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def process_record(record):
    fields = record["fields"]
    name = fields.get("name", "").strip()
    company = fields.get("company name", "").strip()
    email = fields.get("email", "").strip()
    website = fields.get("website", "").strip()
    web_copy = fields.get("web copy", "").strip()

    # Normalize and scrape if needed
    if website and not website.startswith("http"):
        website = normalize_url(website)
        homepage = scrape_visible_text(website)
        services = scrape_visible_text(website + "/services")
        full_copy = homepage + "\n" + services
        airtable.update(record["id"], {"web copy": full_copy})
        web_copy = full_copy

    # Validate again after scrape
    valid, missing = is_valid_lead(record)
    if not valid:
        print(f"❌ Skipping {name or '[no name]'} @ {company or '[no company]'} (missing: {', '.join(missing)})")
        return

    prompt = generate_prompt(name, company, web_copy)
    response = openai.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    email_body = response.choices[0].message.content

    subject = f"Quick hello from Toon Theory"
    send_email(email, subject, email_body)

    now = (datetime.utcnow() + TZ_OFFSET).replace(microsecond=0)
    followup1 = now + timedelta(days=3)
    followup2 = followup1 + timedelta(days=4)

    airtable.update(record["id"], {
        "initial date": now.isoformat(),
        "follow-up 1 date": followup1.isoformat(),
        "follow-up 2 date": followup2.isoformat(),
        "status": "sent",
    })

    print(f"✅ Sent to {name} @ {company} ({email})")
    sleep(random.randint(*DELAY_RANGE))


def main():
    records = airtable.get(view=AIRTABLE_VIEW_NAME, sort=["initial date"])
    print(f"🔍 Total leads found: {len(records)}")

    sent_today = 0
    for record in records:
        if sent_today >= MAX_EMAILS_PER_DAY:
            break

        fields = record.get("fields", {})
        if fields.get("status", "").lower() == "sent":
            continue

        process_record(record)
        sent_today += 1


if __name__ == "__main__":
    main()
