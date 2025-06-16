import os
import random
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from airtable import Airtable
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()

# Airtable config
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
AIRTABLE_VIEW_NAME = os.getenv('AIRTABLE_VIEW_NAME')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# Email config
SMTP_SERVER = 'smtp.zoho.com'
SMTP_PORT = 587
SMTP_USERNAME = 'hello@toontheory.com'
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Groq config
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = "llama3-70b-8192"

def scrape_visible_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts, styles, header, nav, and footer
        for tag in soup(['script', 'style', 'header', 'nav', 'footer', 'form']):
            tag.decompose()

        # Get all visible text
        visible_text = ' '.join(chunk.strip() for chunk in soup.stripped_strings)
        return visible_text[:8000]  # Limit to 8000 characters max
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def get_groq_response(prompt):
    import openai
    openai.api_key = GROQ_API_KEY
    response = openai.ChatCompletion.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes natural, plain-English cold emails using scraped web copy."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def send_email(to_address, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        print(f"Email sent to {to_address}")

def generate_prompt(web_copy, name, company):
    return f"""
Write a short, plain-English cold email introducing Toon Theory to {name} from {company}. Use this scraped text as the reference to personalize the message:

{web_copy}

Keep it friendly, under 150 words. Avoid using em dashes. Use a casual, conversational tone.
"""

def main():
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get(view=AIRTABLE_VIEW_NAME)['records']

    print(f"🟡 Total leads found: {len(records)}")

    for record in records:
        fields = record.get('fields', {})
        name = fields.get('name')
        company = fields.get('company name')
        email = fields.get('email')
        website = fields.get('website')
        web_copy = fields.get('web copy')
        status = fields.get('status', '').lower()

        if not all([name, company, email, website]):
            continue  # Essential info is missing

        if status not in ['', 'not contacted']:
            continue

        # Scrape if web copy is missing
        if not web_copy:
            homepage = scrape_visible_text(website)
            services_page = scrape_visible_text(website.rstrip('/') + '/services')
            full_copy = homepage + '\n' + services_page
            airtable.update(record['id'], {'web copy': full_copy})
            web_copy = full_copy
            print(f"✅ Scraped and updated web copy for {company}")

        # Generate and send email
        prompt = generate_prompt(web_copy, name, company)
        message = get_groq_response(prompt)

        subject = f"Quick idea for {company}"
        send_email(email, subject, message)

        now_str = datetime.now().strftime('%Y-%m-%d')
        followup1 = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        followup2 = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

        airtable.update(record['id'], {
            'initial date': now_str,
            'follow-up 1 date': followup1,
            'follow-up 2 date': followup2,
            'status': 'initial sent'
        })

        # Wait random 2–5 minutes
        delay = random.randint(120, 300)
        print(f"⏱ Waiting {delay}s before next...")
        time.sleep(delay)

if __name__ == '__main__':
    main()
