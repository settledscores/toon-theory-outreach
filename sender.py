import json
import smtplib
import imaplib
import email
import os
import time
import base64
import random
import requests
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import make_msgid
from zoneinfo import ZoneInfo

# === Load Secrets ===
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
IMAP_PORT = int(os.environ["IMAP_PORT"])
IMAP_SERVER = os.environ["IMAP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_SERVER = os.environ["SMTP_SERVER"]
ZOHO_CLIENT_ID = os.environ["ZOHO_CLIENT_ID"]
ZOHO_CLIENT_SECRET = os.environ["ZOHO_CLIENT_SECRET"]
ZOHO_REFRESH_TOKEN = os.environ["ZOHO_REFRESH_TOKEN"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

# === Constants ===
LEADS_FILE = "leads/scraped_leads.json"
TIMEZONE = ZoneInfo("Africa/Lagos")
TODAY = datetime.now(TIMEZONE).date()
WEEKDAY = TODAY.weekday()  # 0 = Monday, 6 = Sunday

# === Daily Quotas ===
DAILY_PLAN = {
    0: {"initial": 30, "fu1": 0, "fu2": 0},   # Monday
    1: {"initial": 30, "fu1": 0, "fu2": 0},   # Tuesday
    2: {"initial": 15, "fu1": 15, "fu2": 0},  # Wednesday
    3: {"initial": 15, "fu1": 15, "fu2": 0},  # Thursday
    4: {"initial": 0, "fu1": 15, "fu2": 15},  # Friday
}
TODAY_PLAN = DAILY_PLAN.get(WEEKDAY, {"initial": 0, "fu1": 0, "fu2": 0})

# === Subject Pools ===
INITIAL_SUBJECTS = [
    "Let’s make your message stick", "A quick thought for your next project",
    "Helping your ideas stick visually", "Turn complex into simple (in 90 seconds)",
    "Your story deserves to be told differently", "How about a different approach to your messaging?",
    "Making your story unforgettable", "Bring your message to life — visually",
    "Your pitch deserves more than plain text", "What if your message spoke in pictures?",
    "Visual stories make better first impressions", "Helping businesses explain what makes them different",
    "Cut through noise with visual storytelling", "A visual idea for {company}",
    "Explainers that make people pay attention", "What if you could show it instead of tell it?",
    "Here’s an idea worth testing", "Explaining complex stuff with simple visuals",
    "Is your message reaching its full potential?", "A story-first idea for {company}",
    "Cut through mess and set your message free", "Idea: use animation to make your message hit harder",
    "This might help supercharge your next big project at {company}",
    "How do you explain what {company} does?", "Let’s make it click visually"
]
FU1_SUBJECTS = [
    "Just Checking In, {name}", "Thought I’d Follow Up, {name}", "Any Thoughts On This, {name}?",
    "Circling Back, {name}", "Sketching Some Ideas For {company}", "A Quick Follow-Up, {name}",
    "Any Interest In This, {name}?", "Here’s That Idea Again, {name}",
    "Are You Still Open To This, {name}?", "Quick Check-In, {name}",
    "Following Up On That Idea For {company}", "Nudging This Up Your Inbox, {name}",
    "Revisiting, Just In Case You Missed This The Last Time, {name}", "{name}, Got A Sec?",
    "Circling Back To That Idea For {company}", "A Follow-Up From Toon Theory, {name}"
]
FU2_SUBJECTS = [
    "Any thoughts on this, {name}?", "Checking back in, {name}", "Quick follow-up, {name}",
    "Still curious if this helps", "Wondering if this sparked anything", "Visual storytelling, still on the table?",
    "A quick nudge your way", "Happy to mock something up", "Short reminder, {name}",
    "Just revisiting this idea", "Whiteboard sketch still an option?", "No pressure, just following up",
    "Back with another nudge", "A final nudge, {name}", "Hoping this reached you",
    "Revisiting that animation idea", "Let me know if now's better", "Still worth exploring?",
    "Quick question on our last email", "Still around if helpful", "Do you want me to close this out?",
    "Open to creative pitches?", "Just in case it got buried"
]

# === Token Logic ===
def get_zoho_access_token():
    res = requests.post("https://accounts.zoho.com/oauth/v2/token", data={
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    })
    res.raise_for_status()
    return res.json()["access_token"]

def get_auth_string(email, token):
    return base64.b64encode(f"user={email}\1auth=Bearer {token}\1\1".encode()).decode()

def send_email(recipient, subject, content, in_reply_to=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = recipient
    msg.set_content(content)
    msg_id = make_msgid(domain="toontheory.com")[1:-1]
    msg["Message-ID"] = f"<{msg_id}>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    token = get_zoho_access_token()
    auth_string = get_auth_string(EMAIL_ADDRESS, token)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.docmd("AUTH", "XOAUTH2 " + auth_string)
        smtp.send_message(msg)

    return msg_id

def check_replies(message_ids):
    seen = set()
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as imap:
        imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        imap.select("INBOX")
        typ, data = imap.search(None, "ALL")
        for num in data[0].split():
            typ, msg_data = imap.fetch(num, "(RFC822)")
            if typ != "OK": continue
            msg = email.message_from_bytes(msg_data[0][1])
            headers = (msg.get("In-Reply-To") or "") + (msg.get("References") or "")
            for mid in message_ids:
                if f"<{mid}>" in headers:
                    seen.add(mid)
    return seen

# === Load Leads ===
with open(LEADS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
leads = data.get("records", [])
for lead in leads:
    for k in [
        "email", "email 1", "email 2", "email 3",
        "message id", "message id 2", "message id 3",
        "initial date", "follow-up 1 date", "follow-up 2 date",
        "reply", "business name", "first name"
    ]:
        lead.setdefault(k, "")

# === Detect Replies ===
all_ids = [(lead["message id"], "after initial") for lead in leads if lead["message id"]] + \
          [(lead["message id 2"], "after FU1") for lead in leads if lead["message id 2"]] + \
          [(lead["message id 3"], "after FU2") for lead in leads if lead["message id 3"]]
replied = check_replies([mid for mid, _ in all_ids])
for lead in leads:
    if lead["reply"] not in ["after initial", "after FU1", "after FU2"]:
        for key, label in [("message id", "after initial"), ("message id 2", "after FU1"), ("message id 3", "after FU2")]:
            if lead[key] and lead[key] in replied:
                lead["reply"] = label
    if not lead["reply"]:
        lead["reply"] = "no reply"

# === Eligibility Check ===
def can_send_initial(lead):
    return not lead["initial date"] and lead["email 1"]

def can_send_followup(lead, step):
    if not lead["email"] or lead["reply"] != "no reply":
        return False
    prev_key = "initial date" if step == 2 else "follow-up 1 date"
    msg_id_key = "message id" if step == 2 else "message id 2"
    next_key = f"follow-up {step} date"
    if not lead[prev_key] or not lead[msg_id_key] or lead[next_key]:
        return False
    send_day = datetime.strptime(lead[prev_key], "%Y-%m-%d").date() + timedelta(days=3)
    while send_day.weekday() > 4:
        send_day += timedelta(days=1)
    return TODAY == send_day

# === Send Queue ===
queue = []

for lead in leads:
    if len([q for q in queue if q[0] == "fu2"]) < TODAY_PLAN["fu2"] and can_send_followup(lead, 3):
        queue.append(("fu2", lead))
for lead in leads:
    if len([q for q in queue if q[0] == "fu1"]) < TODAY_PLAN["fu1"] and can_send_followup(lead, 2):
        queue.append(("fu1", lead))
for lead in leads:
    if len([q for q in queue if q[0] == "initial"]) < TODAY_PLAN["initial"] and can_send_initial(lead):
        queue.append(("initial", lead))

# === Send Emails ===
for kind, lead in queue:
    time.sleep(random.uniform(2, 5))
    dt = datetime.now(TIMEZONE).replace(
        hour=random.randint(14, 18),
        minute=random.randint(0, 59),
        second=random.randint(1, 59)
    )
    wait = (dt - datetime.now(TIMEZONE)).total_seconds()
    if not os.environ.get("GITHUB_ACTIONS") and wait > 0:
        time.sleep(wait)

    if kind == "initial":
        subject = random.choice(INITIAL_SUBJECTS).format(company=lead["business name"])
        msgid = send_email(lead["email"], subject, lead["email 1"])
        lead["message id"] = msgid
        lead["initial date"] = TODAY.isoformat()
    elif kind == "fu1":
        subject = random.choice(FU1_SUBJECTS).format(name=lead["first name"], company=lead["business name"])
        msgid = send_email(lead["email"], subject, lead["email 2"], f"<{lead['message id']}>")
        lead["message id 2"] = msgid
        lead["follow-up 1 date"] = TODAY.isoformat()
    elif kind == "fu2":
        subject = random.choice(FU2_SUBJECTS).format(name=lead["first name"], company=lead["business name"])
        msgid = send_email(lead["email"], subject, lead["email 3"], f"<{lead['message id 2']}>")
        lead["message id 3"] = msgid
        lead["follow-up 2 date"] = TODAY.isoformat()

# === Save JSON ===
data["records"] = leads
data["total"] = len(leads)
data["scraped_at"] = datetime.now().isoformat()

with open(LEADS_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
