import os
import json
import smtplib
import imaplib
import email
import random
from email.message import EmailMessage
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

# === Config ===
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", EMAIL_ADDRESS)
SMTP_SERVER = "smtppro.zoho.com"
SMTP_PORT = 465
IMAP_SERVER = "imappro.zoho.com"
LEADS_FILE = "leads/scraped_leads.ndjson"
TIMEZONE = ZoneInfo("Africa/Lagos")
NOW = datetime.now(TIMEZONE)
TODAY = NOW.date()
NOW_TIME = NOW.strftime("%H:%M")
WEEKDAY = TODAY.weekday()
BASE_START_TIME = time(13, 30)
END_TIME = time(20, 30)
FINAL_END_TIME = time(20, 30)

# === Subject Pool ===
initial_subjects = [
    "Ever seen a pitch drawn out?", "You’ve probably never gotten an email like this",
    "This might sound odd, but useful", "Not sure if this will land, but here goes",
    "You might like what I’ve been sketching", "This idea’s been stuck in my head",
    "Bet you haven’t tried this approach yet", "What if your next pitch was drawn?",
    "This has worked weirdly well for others", "A small idea that might punch above its weight",
    "Is this a weird idea? Maybe.", "Is this worth trying? Probably.",
    "Thought of you while doodling", "This one might be a stretch, but could work",
    "Felt like this might be your kind of thing", "Kind of random, but hear me out",
    "If you're up for an odd idea", "Not a pitch, just something I had to share",
    "This one’s a bit out there", "Saw what you’re doing, had to send this",
    "Wanna try something weird?", "Ever tried sketching your message?",
    "Quick thought: could sketches help?",
    "This idea has been stuck in my head", "Quick idea you probably haven’t seen before",
    "Hope this doesn’t sound too off", "Could this work for your pitch?",
    "Bit of an odd angle, but may click", "Does this feel off-brand or on-point?",
    "Just playing with this angle",
]
random.shuffle(initial_subjects)

def read_multiline_ndjson(path):
    records, buffer = [], ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): 
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    records.append(json.loads(buffer))
                except:
                    pass
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")

def is_ascii_email(email_addr):
    try:
        email_addr.encode('ascii')
        return True
    except:
        return False

def is_minimal_url_only(lead):
    return list(lead.keys()) == ["website url"] or (
        "website url" in lead and all((k == "website url" or not str(v).strip()) for k, v in lead.items())
    )

def next_subject(pool, **kwargs):
    template = pool.pop(0)
    pool.append(template)
    return template.format(**kwargs)

def can_send_initial(lead):
    return not lead.get("initial date") and lead.get("email") and lead.get("email 1")

def can_send_followup(lead, step):
    if lead.get("reply", "no reply") != "no reply" or not lead.get("email"):
        return False
    try:
        if step == 2:
            if not lead.get("initial date") or lead.get("follow-up 1 date") or not lead.get("email 2"):
                return False
            last_dt = datetime.strptime(f"{lead['initial date']} {lead['initial time']}", "%Y-%m-%d %H:%M")
            return NOW >= last_dt + timedelta(minutes=5)
        elif step == 3:
            if not lead.get("follow-up 1 date") or lead.get("follow-up 2 date") or not lead.get("email 3"):
                return False
            last_dt = datetime.strptime(f"{lead['follow-up 1 date']} {lead['follow-up 1 time']}", "%Y-%m-%d %H:%M")
            return NOW >= last_dt + timedelta(minutes=5)
    except:
        return False
    return False

def detect_reply_status(leads):
    print("[IMAP] Checking for replies...")
    try:
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            for folder in ['INBOX', 'SPAM']:
                mail.select(folder)
                result, data = mail.search(None, 'ALL')
                if result != "OK": 
                    continue
                for num in data[0].split():
                    res, msg_data = mail.fetch(num, "(RFC822)")
                    if res != "OK": 
                        continue
                    raw = email.message_from_bytes(msg_data[0][1])
                    from_addr = email.utils.parseaddr(raw.get("From", ""))[1].lower()
                    subject = (raw.get("Subject") or "").lower()
                    body = ""
                    if raw.is_multipart():
                        for part in raw.walk():
                            if part.get_content_type() == "text/plain":
                                body += part.get_payload(decode=True).decode(errors="ignore")
                    else:
                        body = raw.get_payload(decode=True).decode(errors="ignore")
                    for lead in leads:
                        lead_email = lead.get("email", "").lower()
                        if not lead_email: 
                            continue
                        matched = (
                            lead_email in from_addr or
                            lead_email in subject or
                            lead_email in body
                        )
                        if matched:
                            if lead.get("follow-up 2 date"):
                                lead["reply"] = "after FU2"
                            elif lead.get("follow-up 1 date"):
                                lead["reply"] = "after FU1"
                            elif lead.get("initial date"):
                                lead["reply"] = "after initial"
    except Exception as e:
        print(f"[IMAP] Error: {e}")

def send_email(to, subject, content):
    if not is_ascii_email(to):
        raise ValueError("Non-ASCII address skipped")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg.set_content(content)
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, from_addr=FROM_EMAIL)

# === Load and preprocess leads ===
leads = read_multiline_ndjson(LEADS_FILE)
for lead in leads:
    if is_minimal_url_only(lead):
        continue
    for f in ["email", "email 1", "email 2", "email 3", "business name", "first name", "subject",
              "initial date", "follow-up 1 date", "follow-up 2 date",
              "initial time", "follow-up 1 time", "follow-up 2 time", "reply"]:
        lead.setdefault(f, "")
    if not lead["reply"]:
        lead["reply"] = "no reply"
    for key in list(lead):
        if key.startswith(("message id", "in-reply-to", "references")):
            del lead[key]

detect_reply_status(leads)

BASE_QUOTA = 50
backlogs = sum(1 for l in leads if can_send_followup(l, 2) or can_send_followup(l, 3))
recent_initials = sum(
    1 for l in leads
    if l.get("initial date") in [
        (TODAY - timedelta(days=d)).isoformat()
        for d in range(1, 6) if (TODAY - timedelta(days=d)).weekday() < 5
    ]
)
extra_quota = min(20, backlogs)
if recent_initials < 20:
    extra_quota += 20
DAILY_QUOTA = BASE_QUOTA + extra_quota
sent_today = sum(1 for l in leads if TODAY.isoformat() in [
    l.get("initial date"), l.get("follow-up 1 date"), l.get("follow-up 2 date")
])

print(f"[Quota] Base: {BASE_QUOTA}, Backlogs: {backlogs}, Recent Initials: {recent_initials}")
print(f"[Quota] Extra: {extra_quota}, Total: {DAILY_QUOTA}")
print(f"[Quota] Sent Today: {sent_today}")

minutes_needed = DAILY_QUOTA * 7
start = datetime.combine(TODAY, BASE_START_TIME) - timedelta(minutes=minutes_needed)
end = datetime.combine(TODAY, END_TIME) + timedelta(minutes=(DAILY_QUOTA - BASE_QUOTA) * 7)
if not start.time() <= NOW.time() <= min(end.time(), FINAL_END_TIME):
    exit(0)

queue = []
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

print(f"[Process] {len(queue)} message(s) to send...")

for kind, lead in queue:
    try:
        if kind == "initial":
            subject = next_subject(initial_subjects, company=lead["business name"])
            send_email(lead["email"], subject, lead["email 1"])
            lead["subject"] = subject
            lead["initial date"] = TODAY.isoformat()
            lead["initial time"] = NOW_TIME
        elif kind == "fu1":
            subject = f"Re: {lead['subject']}" if lead["subject"] else "Just checking in"
            send_email(lead["email"], subject, lead["email 2"])
            lead["follow-up 1 date"] = TODAY.isoformat()
            lead["follow-up 1 time"] = NOW_TIME
        elif kind == "fu2":
            subject = f"Re: {lead['subject']}" if lead["subject"] else "Just circling back"
            send_email(lead["email"], subject, lead["email 3"])
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME
    except Exception as e:
        print(f"[Error] Failed to send {kind} to {lead.get('email')}: {e}")

print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
