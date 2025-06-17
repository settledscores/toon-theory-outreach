import os
import random
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from airtable import Airtable
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEZONE_OFFSET = 1  # WAT = UTC+1

openai.api_key = OPENAI_API_KEY
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

def prepend_https(url):
    return url if url.startswith("http") else f"https://{url.strip()}"

def scrape_visible_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(prepend_https(url), headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["nav", "footer", "header", "script", "style", "noscript", "a", "link", "img", "button"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())
    except Exception as e:
        print(f"⚠️ Failed to scrape {url}: {e}")
        return ""

def generate_prompt(name, company, website_copy):
    return (
        f"You're writing a short email to {name} from {company}. "
        f"Their website says: {website_copy[:1200]}... "
        "You run Toon Theory, a UK-based whiteboard animation studio. "
        "Write a friendly cold email using clear English, no buzzwords, and no em dashes. Keep it natural and brief."
    )

def generate_email_content(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write in clear, concise English with a friendly tone. Avoid em dashes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def send_email(to_address, subject, body):
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.zoho.com", 465) as smtp:
        smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        smtp.send_message(msg)

def send_randomized_email(name, company, email, website, website_copy):
    prompt = generate_prompt(name, company, website_copy)
    content = generate_email_content(prompt)
    subject = content.splitlines()[0].strip()[:60] if content else "Quick hello"

    send_email(email, subject, content)
    print(f"✅ Sent to {email} — {subject}")

def process_leads():
    leads = airtable.get_all(view="Grid view")
    print(f"🔍 Total leads found: {len(leads)}")

    for record in leads:
        fields = record["fields"]
        name = fields.get("name", "").strip()
        company_name = fields.get("company name", "").strip()
        email = fields.get("email", "").strip()
        website = fields.get("website", "").strip()
        web_copy = fields.get("web copy", "").strip()

        if not all([name, company_name, email, website, web_copy]):
            print("⚠️ Skipping due to missing required fields")
            continue

        # Only send to leads who haven't been contacted yet
        if "initial date" not in fields:
            send_randomized_email(name, company_name, email, website, web_copy)
            today = (datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)).strftime("%Y-%m-%d")
            follow1 = (datetime.utcnow() + timedelta(days=3, hours=TIMEZONE_OFFSET)).strftime("%Y-%m-%d")
            follow2 = (datetime.utcnow() + timedelta(days=7, hours=TIMEZONE_OFFSET)).strftime("%Y-%m-%d")
            airtable.update(record["id"], {
                "initial date": today,
                "follow-up 1 date": follow1,
                "follow-up 2 date": follow2,
                "status": "Sent"
            })

def update_web_copy():
    leads = airtable.get_all(view="Grid view")
    for record in leads:
        fields = record["fields"]
        website = fields.get("website", "").strip()
        web_copy = fields.get("web copy", "").strip()

        if website and not web_copy:
            scraped = scrape_visible_text(website)
            if scraped:
                airtable.update(record["id"], {"web copy": scraped})
                print(f"📝 Updated web copy for {website}")

if __name__ == "__main__":
    update_web_copy()
    process_leads()
