import json
import smtplib
import imaplib
import email
import os
import random
from datetime import datetime, timedelta, time
from email.message import EmailMessage
from email.utils import make_msgid
from zoneinfo import ZoneInfo

# === Config ===
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", EMAIL_ADDRESS)
IMAP_SERVER = os.environ["IMAP_SERVER"]
IMAP_PORT = int(os.environ["IMAP_PORT"])
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])

LEADS_FILE = "leads/scraped_leads.ndjson"
TIMEZONE = ZoneInfo("Africa/Lagos")
NOW = datetime.now(TIMEZONE)
TODAY = NOW.date()
NOW_TIME = NOW.strftime("%H:%M")
WEEKDAY = TODAY.weekday()

if not time(14, 0) <= NOW.time() <= time(19, 30):
    print(f"[Skip] Outside allowed window ({NOW.time()} WAT), exiting.")
    exit(0)

# === Subject Pools ===
initial_subjects = [
    "Let’s make your message stick", "Helping your ideas stick visually",
    "Turn complex into simple (in 90 seconds)", "Your story deserves to be told differently",
    "How about a different approach to your messaging?", "Making your message unforgettable",
    "Bring your message to life — visually", "Your pitch deserves more than plain text",
    "Visual stories make better first impressions", "Helping businesses explain what makes them different",
    "Cut through noise with visual storytelling", "Explainers that make people pay attention",
    "What if you could show it instead of tell it?", "Here’s an idea worth testing",
    "Explaining complex stuff with simple visuals", "Is your message reaching it's full potential?",
    "A story-first idea for {company}", "Cut through mess and set your message free",
    "Idea: use animation to make your message hit harder",
    "This might help supercharge your next big project at {company}",
    "How do you explain what {company} does?"
]

random.shuffle(initial_subjects)

# === Subject Rotation ===
def next_subject(pool, **kwargs):
    if not pool:
        return None
    template = pool.pop(0)
    pool.append(template)
    return template.format(**kwargs)

# === File Helpers ===
def read_multiline_ndjson(path):
    records = []
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    records.append(json.loads(buffer))
                except Exception as e:
                    print(f"[Skip] Corrupt block: {e}")
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")

# === Email Functions ===
def send_email(to_email, subject, content, in_reply_to=None):
    print(f"[Send] Preparing to send to {to_email} | Subject: {subject}")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(content)
    msg_id = make_msgid(domain=FROM_EMAIL.split("@")[-1])[1:-1]
    msg["Message-ID"] = f"<{msg_id}>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, from_addr=FROM_EMAIL)
    print(f"[Send] Email sent to {to_email}")
    return msg_id

def check_replies(message_ids):
    seen = set()
    print("[IMAP] Checking replies in inbox and spam...")
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as imap:
        imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        for folder in ["INBOX", "SPAM", "Junk", "[Gmail]/Spam"]:
            try:
                imap.select(folder)
                typ, data = imap.search(None, "ALL")
                if typ != "OK":
                    continue
                for num in data[0].split():
                    typ, msg_data = imap.fetch(num, "(RFC822)")
                    if typ != "OK":
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    headers = (msg.get("In-Reply-To") or "") + (msg.get("References") or "")
                    for mid in message_ids:
                        if f"<{mid}>" in headers:
                            seen.add(mid)
            except:
                continue
    return seen

# === Load & Prep Leads ===
leads = read_multiline_ndjson(LEADS_FILE)
for lead in leads:
    for field in [
        "email", "email 1", "email 2", "email 3", "business name", "first name",
        "message id", "message id 2", "message id 3", "subject",
        "initial date", "follow-up 1 date", "follow-up 2 date",
        "initial time", "follow-up 1 time", "follow-up 2 time", "reply"
    ]:
        lead.setdefault(field, "")

# === Update Replies ===
print("[Replies] Updating reply status...")
all_ids = [(lead["message id"], "after initial") for lead in leads if lead["message id"]] + \
          [(lead["message id 2"], "after FU1") for lead in leads if lead["message id 2"]] + \
          [(lead["message id 3"], "after FU2") for lead in leads if lead["message id 3"]]
replied = check_replies([mid for mid, _ in all_ids])
for lead in leads:
    if lead["reply"] not in ["after initial", "after FU1", "after FU2"]:
        for k, label in [("message id", "after initial"), ("message id 2", "after FU1"), ("message id 3", "after FU2")]:
            if lead[k] and lead[k] in replied:
                lead["reply"] = label
    if not lead["reply"]:
        lead["reply"] = "no reply"

# === Count Sent Today ===
sent_today = sum(
    1 for l in leads
    if l.get("initial date") == TODAY.isoformat() or
       l.get("follow-up 1 date") == TODAY.isoformat() or
       l.get("follow-up 2 date") == TODAY.isoformat()
)

# === Send Eligibility ===
def can_send_initial(lead):
    return not lead["initial date"] and lead.get("email") and lead.get("email 1") and WEEKDAY != 4

def can_send_followup(lead, step):
    if lead["reply"] != "no reply" or not lead.get("email"):
        return False

    if step == 2:
        prev_date_key = "initial date"
        msg_id_key = "message id"
        curr_date_key = "follow-up 1 date"
        content_key = "email 2"
    elif step == 3:
        prev_date_key = "follow-up 1 date"
        msg_id_key = "message id 2"
        curr_date_key = "follow-up 2 date"
        content_key = "email 3"
    else:
        return False

    if not (lead[prev_date_key] and lead[msg_id_key] and not lead[curr_date_key] and lead.get(content_key)):
        return False

    start_date = datetime.strptime(lead[prev_date_key], "%Y-%m-%d").date()
    ideal_send_date = start_date + timedelta(days=step)
    actual_send_date = ideal_send_date

    rollover_days = 0
    while actual_send_date.weekday() >= 5:
        actual_send_date += timedelta(days=1)
        rollover_days += 1

    if step == 3 and rollover_days > 0:
        actual_send_date -= timedelta(days=min(rollover_days, 2))
        while actual_send_date.weekday() >= 5:
            actual_send_date += timedelta(days=1)

    return TODAY >= actual_send_date

# === Build Queue ===
print("[Queue] Building one-message queue...")
queue = []
if sent_today < 30:
    for step, label in [(3, "fu2"), (2, "fu1"), (0, "initial")]:
        for lead in leads:
            if label == "initial" and can_send_initial(lead):
                queue = [("initial", lead)]
                break
            elif label == "fu1" and can_send_followup(lead, 2):
                queue = [("fu1", lead)]
                break
            elif label == "fu2" and can_send_followup(lead, 3):
                queue = [("fu2", lead)]
                break
        if queue:
            break

# === Send Message ===
print(f"[Process] {len(queue)} message(s) to send...")
for kind, lead in queue:
    try:
        if kind == "initial":
            subject = next_subject(initial_subjects, company=lead["business name"])
            msgid = send_email(lead["email"], subject, lead["email 1"])
            lead["message id"] = msgid
            lead["subject"] = subject
            lead["initial date"] = TODAY.isoformat()
            lead["initial time"] = NOW_TIME
        elif kind == "fu1":
            subject = f"Re: {lead['subject']}"
            msgid = send_email(lead["email"], subject, lead["email 2"], f"<{lead['message id']}>")
            lead["message id 2"] = msgid
            lead["follow-up 1 date"] = TODAY.isoformat()
            lead["follow-up 1 time"] = NOW_TIME
        elif kind == "fu2":
            subject = f"Re: {lead['subject']}"
            msgid = send_email(lead["email"], subject, lead["email 3"], f"<{lead['message id 2']}>")
            lead["message id 3"] = msgid
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME
    except Exception as e:
        print(f"[Error] Failed to send to {lead.get('email', 'UNKNOWN')}: {e}")

# === Save Output ===
print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
