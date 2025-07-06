import json
import smtplib
import imaplib
import email
import os
import random
from datetime import datetime, timedelta
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
TODAY = datetime.now(TIMEZONE).date()
WEEKDAY = TODAY.weekday()

DAILY_PLAN = {
    0: {"initial": 30, "fu1": 0, "fu2": 0},
    1: {"initial": 30, "fu1": 0, "fu2": 0},
    2: {"initial": 15, "fu1": 15, "fu2": 0},
    3: {"initial": 15, "fu1": 15, "fu2": 0},
    4: {"initial": 0, "fu1": 15, "fu2": 15},
    6: {"initial": 2, "fu1": 0, "fu2": 0},    # Sunday ← ✅ ADD THIS
}
TODAY_PLAN = DAILY_PLAN.get(WEEKDAY, {"initial": 0, "fu1": 0, "fu2": 0})

# === Subject Lines ===
INITIAL_SUBJECTS = [
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

FU1_SUBJECTS = [
    "Just Checking In, {name}", "Thought I’d Follow Up, {name}", "Any Thoughts On This, {name}?",
    "Circling Back, {name}", "Sketching Some Ideas For {company}", "A Quick Follow-Up, {name}",
    "Any Interest In This, {name}?", "Here’s That Idea Again, {name}", "Are You Still Open To This, {name}?",
    "Quick Check-In, {name}", "Following Up On That Idea For {company}", "Nudging This Up Your Inbox, {name}",
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

# === Utils ===
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
                    record = json.loads(buffer)
                    records.append(record)
                except Exception as e:
                    print(f"[Skip] Corrupt block: {e}")
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")

# === Email Sender ===
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

# === IMAP Checker ===
def check_replies(message_ids):
    seen = set()
    print("[IMAP] Checking replies...")
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as imap:
        imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        imap.select("INBOX")
        typ, data = imap.search(None, "ALL")
        if typ != "OK":
            return seen
        for num in data[0].split():
            typ, msg_data = imap.fetch(num, "(RFC822)")
            if typ != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            headers = (msg.get("In-Reply-To") or "") + (msg.get("References") or "")
            for mid in message_ids:
                if f"<{mid}>" in headers:
                    seen.add(mid)
    return seen

# === Load and Initialize ===
print("[Load] Reading leads file...")
leads = read_multiline_ndjson(LEADS_FILE)

for lead in leads:
    for field in [
        "email", "email 1", "email 2", "email 3", "business name", "first name",
        "message id", "message id 2", "message id 3",
        "initial date", "follow-up 1 date", "follow-up 2 date", "reply"
    ]:
        lead.setdefault(field, "")

# === Check Replies ===
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

# === Eligibility Checks ===
def can_send_initial(lead):
    return not lead["initial date"] and lead.get("email 1") and lead.get("email")

def can_send_followup(lead, step):
    if lead["reply"] != "no reply" or not lead.get("email"):
        return False
    prev_key = "initial date" if step == 2 else "follow-up 1 date"
    msg_id_key = "message id" if step == 2 else "message id 2"
    next_key = f"follow-up {step} date"
    email_key = f"email {step}"
    if not (lead[prev_key] and lead[msg_id_key] and not lead[next_key] and lead.get(email_key)):
        return False
    send_day = datetime.strptime(lead[prev_key], "%Y-%m-%d").date() + timedelta(days=3)
    while send_day.weekday() > 4:
        send_day += timedelta(days=1)
    return TODAY == send_day

# === Queue ===
print("[Queue] Building send queue...")
counts = {"initial": 0, "fu1": 0, "fu2": 0}
queue = []
for lead in leads:
    if counts["fu2"] < TODAY_PLAN["fu2"] and can_send_followup(lead, 3):
        queue.append(("fu2", lead)); counts["fu2"] += 1
    elif counts["fu1"] < TODAY_PLAN["fu1"] and can_send_followup(lead, 2):
        queue.append(("fu1", lead)); counts["fu1"] += 1
    elif counts["initial"] < TODAY_PLAN["initial"] and can_send_initial(lead):
        queue.append(("initial", lead)); counts["initial"] += 1
    if all(counts[k] >= TODAY_PLAN[k] for k in ["initial", "fu1", "fu2"]):
        break

# === Send ===
print(f"[Process] {len(queue)} messages to send...")
for kind, lead in queue:
    try:
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
    except Exception as e:
        print(f"[Error] Failed to send to {lead.get('email', 'UNKNOWN')}: {e}")

# === Save ===
print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
