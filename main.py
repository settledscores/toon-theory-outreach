import os
import smtplib
import imaplib
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pytz import timezone
from dateutil.parser import parse
from airtable import Airtable
import random

CONSTANTS

AIRTABLE_API_KEY = "pat5066FrEhKfGgm6.163765e4f2e56e31d591c3005be3d4570875d87dec201799e6c870531ee84f18" AIRTABLE_BASE_ID = "apphIwzbnFgC6uUo8" AIRTABLE_TABLE_NAME = "Toon Theory" GROQ_API_KEY = os.getenv("GROQ_API_KEY") EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS") EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") SMTP_SERVER = "smtppro.zoho.com" SMTP_PORT = 465 IMAP_SERVER = "imappro.zoho.com" IMAP_PORT = 993 TIMEZONE = timezone("Africa/Lagos")

Connect Airtable

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

Prompt template

PROMPT_TEMPLATE = """ You're helping a whiteboard animation studio write a cold outreach email.

Here is their base email:

Hi {name},

I’ve been following {company} lately, and your ability to make {summary} really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on {angle}, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to: {use_cases}

If you're open to it, I’d love to share a few tailored samples or sketch out what this could look like for {company}'s brand voice.

Warm regards, Trent Founder, Toon Theory www.toontheory.com Whiteboard Animation For The Brands People Trust

Based on the website content below, fill in the missing parts in the email with clear, natural language.

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content: {web_copy} """

def scrape_visible_text(url): try: response = requests.get(url, timeout=10) soup = BeautifulSoup(response.text, "html.parser") for tag in soup(["nav", "footer", "header", "script", "style", "a", "img", "svg"]): tag.decompose() return soup.get_text(separator=" ", strip=True) except Exception as e: print(f"❌ Error scraping {url}: {e}") return ""

def get_combined_webcopy(website): home = scrape_visible_text(website) services = scrape_visible_text(website.rstrip("/") + "/services") return (home + " " + services).strip()

def generate_email_groq(web_copy, name, company): prompt = PROMPT_TEMPLATE.format( name=name, company=company, summary="important ideas feel accessible", angle="simplicity and usability", use_cases="- Showing potential clients how your product works\n- Explaining a key concept in 90 seconds\n- Walking viewers through a tool’s value", web_copy=web_copy ) response = requests.post( "https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={ "model": "mixtral-8x7b-32768", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7 } ) return response.json()["choices"][0]["message"]["content"]

def send_email(recipient, subject, body): msg = MIMEMultipart() msg["From"] = EMAIL_ADDRESS msg["To"] = recipient msg["Subject"] = subject msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())

def alert_trent(subject, body): try: send_email("hello@toontheory.com", subject, body) except Exception as e: print(f"❌ Failed to send alert: {e}")

def has_replied(recipient_email): try: with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail: mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD) mail.select("inbox") typ, data = mail.search(None, f'(FROM "{recipient_email}")') return bool(data[0].split()) except Exception as e: print(f"❌ IMAP error checking replies: {e}") return False

def run_campaign(): leads = airtable.get_all() now = datetime.now(TIMEZONE) print(f"🟡 Total leads found: {len(leads)}")

# Select 1 lead max, randomly, within 2pm–7pm WAT
random.shuffle(leads)
for lead in leads:
    fields = lead.get("fields", {})
    email_addr = fields.get("email")
    status = fields.get("status", "").lower()
    name = fields.get("name", "N/A")
    company = fields.get("company name", "N/A")

    if not email_addr or status in ["replied", "rejected"]:
        continue

    def send_and_update(stage):
        try:
            subject = "Quick idea for your team"
            web_copy = fields.get("web copy") or get_combined_webcopy(fields["website"])
            if not fields.get("web copy"):
                airtable.update(lead["id"], {"web copy": web_copy})

            message = generate_email_groq(web_copy, name, company)
            send_email(email_addr, subject, message)
            alert_trent(f"✅ Sent to {name}", f"Subject: {subject}\n\n{message}")

            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            update = {}
            if stage == "initial":
                update = {
                    "initial date": now_str,
                    "follow-up 1 date": (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "sent"
                }
            elif stage == "followup1":
                update = {
                    "follow-up 2 date": (now + timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "followed up once"
                }
            elif stage == "followup2":
                update = {"status": "followed up twice"}
            airtable.update(lead["id"], update)
        except Exception as e:
            alert_trent(f"❌ Failed for {name}", str(e))

    if not fields.get("initial date"):
        send_and_update("initial")
        break

    if not has_replied(email_addr):
        follow1 = fields.get("follow-up 1 date")
        follow2 = fields.get("follow-up 2 date")

        if follow1:
            f1 = parse(follow1)
            if f1 <= now and not follow2:
                send_and_update("followup1")
                break
        if follow2:
            f2 = parse(follow2)
            if f2 <= now:
                send_and_update("followup2")
                break
    else:
        airtable.update(lead["id"], {"status": "replied"})

if name == "main": run_campaign()
