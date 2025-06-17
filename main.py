import os
import random
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from airtable import Airtable
from dotenv import load_dotenv
import openai

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

# Groq config (OpenAI client)
openai.api_key = os.getenv('GROQ_API_KEY')
GROQ_MODEL = "llama3-70b-8192"

def generate_prompt(web_copy, name, company):
    return f"""
You're helping a whiteboard animation studio write a cold outreach email.

Here is their base email:

Hi {name},

I’ve been following {company} lately, and your ability to make [summary] really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on [angle], I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

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

def get_groq_response(prompt):
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
        print(f"✅ Email sent to {to_address}")

def main():
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all(view=AIRTABLE_VIEW_NAME)
    print(f"🔍 Total leads found: {len(records)}")

    for record in records:
        fields = record.get('fields', {})
        name = fields.get('name')
        company = fields.get('company name')
        email = fields.get('email')
        website = fields.get('website')
        web_copy = fields.get('web copy')
        status = fields.get('status', '').lower()

        if not all([name, company, email, website, web_copy]):
            print("⚠️ Skipping incomplete lead")
            continue

        if status and status not in ['not contacted', '']:
            print(f"⏩ Already processed: {company}")
            continue

        prompt = generate_prompt(web_copy, name, company)
        try:
            message = get_groq_response(prompt)
        except Exception as e:
            print(f"❌ Error generating message for {company}: {e}")
            continue

        subject = f"Quick idea for {company}"

        try:
            send_email(email, subject, message)
        except Exception as e:
            print(f"❌ Error sending email to {email}: {e}")
            continue

        now = datetime.now()
        airtable.update(record['id'], {
            'initial date': now.strftime('%Y-%m-%d'),
            'follow-up 1 date': (now + timedelta(days=3)).strftime('%Y-%m-%d'),
            'follow-up 2 date': (now + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'initial sent'
        })

        wait_time = random.randint(300, 600)
        print(f"⏱ Waiting {wait_time}s before next email...")
        time.sleep(wait_time)

if __name__ == '__main__':
    main()
