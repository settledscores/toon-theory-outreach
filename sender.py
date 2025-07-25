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

BASE_START_TIME = time(13, 0)
END_TIME = time(21, 0)
FINAL_END_TIME = time(21, 0)

if WEEKDAY >= 5:
    exit(0)

initial_subjects = [
    "Ever seen a pitch drawn out?", "You’ve probably never gotten an email like this",
    "This might sound odd, but useful", "Not sure if this will land, but here goes",
    "You might like what I’ve been sketching", "This idea’s been stuck in my head",
    "Bet you haven’t tried this approach yet", "What if your next pitch was drawn?",
    "This has worked weirdly well for others", "A small idea that might punch above its weight",
    "Something about {company} got me thinking", "Is this a weird idea? Maybe.", "Is this worth trying? Probably.",
    "Thought of you while doodling", "This one might be a stretch, but could work",
    "Felt like this might be your kind of thing", "Kind of random, but hear me out",
    "If you're up for an odd idea", "Not a pitch, just something I had to share",
    "This one’s a bit out there", "Saw what you’re doing, had to send this"
]
random.shuffle(initial_subjects)

def next_subject(pool, **kwargs):
    if not pool:
        return None
    template = pool.pop(0)
    pool.append(template)
    return template.format(**kwargs)

def quote_previous_message(new_text, old_text, old_date, old_time, old_sender_name, old_sender_email):
    old_dt = datetime.strptime(f"{old_date} {old_time}", "%Y-%m-%d %H:%M")
    old_dt = old_dt.replace(tzinfo=TIMEZONE)
    formatted_date = old_dt.strftime("%A, %b %d, %Y")
    header_line = f"--- On {formatted_date}, {old_sender_name} <{old_sender_email}> wrote ---"
    quoted = "\n".join(["> " + line for line in old_text.strip().splitlines()])
    return f"""{new_text}

{header_line}
{quoted}"""

def read_multiline_ndjson(path):
    records, buffer = [], ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            buffer += line
            if line.strip().endswith("}"):
                try: records.append(json.loads(buffer))
                except: pass
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")

def send_email(to, subject, content):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg.set_content(content)
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, from_addr=FROM_EMAIL)

def can_send_initial(lead):
    return not lead["initial date"] and lead.get("email") and lead.get("email 1")

def can_send_followup(lead, step):
    if lead["reply"] != "no reply" or not lead.get("email"):
        return False
    if step == 2:
        prev_key, curr_key, content_key = "initial time", "follow-up 1 date", "email 2"
    elif step == 3:
        prev_key, curr_key, content_key = "follow-up 1 time", "follow-up 2 date", "email 3"
    else:
        return False
    if not (lead[prev_key] and not lead[curr_key] and lead.get(content_key)):
        return False
    prev_dt = datetime.strptime(f"{lead['initial date']} {lead[prev_key]}", "%Y-%m-%d %H:%M")
    return NOW >= (prev_dt + timedelta(minutes=5))

def backlog_count(leads):
    return sum(1 for l in leads if can_send_followup(l, 2) or can_send_followup(l, 3))

def initials_sent_in_last_days(n):
    count, day, checked = 0, TODAY - timedelta(days=1), 0
    while checked < n:
        if day.weekday() < 5:
            count += sum(1 for l in leads if l.get("initial date") == day.isoformat())
            checked += 1
        day -= timedelta(days=1)
    return count

# === Load leads ===
leads = read_multiline_ndjson(LEADS_FILE)
for lead in leads:
    for field in [
        "email", "email 1", "email 2", "email 3", "business name", "first name", "subject",
        "initial date", "follow-up 1 date", "follow-up 2 date",
        "initial time", "follow-up 1 time", "follow-up 2 time", "reply"
    ]:
        lead.setdefault(field, "")
    if not lead["reply"]:
        lead["reply"] = "no reply"

BASE_QUOTA = 50
backlogs = backlog_count(leads)
recent_initials = initials_sent_in_last_days(3)
extra_quota = min(20, backlogs)
if recent_initials < 20:
    extra_quota += 20
DAILY_QUOTA = BASE_QUOTA + extra_quota
sent_today = sum(
    1 for l in leads
    if l.get("initial date") == TODAY.isoformat() or
       l.get("follow-up 1 date") == TODAY.isoformat() or
       l.get("follow-up 2 date") == TODAY.isoformat()
)

total_minutes_needed = DAILY_QUOTA * 7
ideal_start = datetime.combine(TODAY, BASE_START_TIME) - timedelta(minutes=total_minutes_needed)
ideal_end = datetime.combine(TODAY, END_TIME) + timedelta(minutes=(DAILY_QUOTA - BASE_QUOTA) * 7)
window_start = ideal_start.time()
window_end = min(ideal_end.time(), FINAL_END_TIME)

if not window_start <= NOW.time() <= window_end:
    exit(0)

queue = []
if sent_today < DAILY_QUOTA:
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
            content = quote_previous_message(
                new_text=lead["email 2"],
                old_text=lead["email 1"],
                old_date=lead["initial date"],
                old_time=lead["initial time"],
                old_sender_name="Trent",
                old_sender_email=FROM_EMAIL
            )
            send_email(lead["email"], subject, content)
            lead["follow-up 1 date"] = TODAY.isoformat()
            lead["follow-up 1 time"] = NOW_TIME
        elif kind == "fu2":
            subject = f"Re: {lead['subject']}" if lead["subject"] else "Just circling back"
            content = quote_previous_message(
                new_text=lead["email 3"],
                old_text=lead["email 2"],
                old_date=lead["follow-up 1 date"],
                old_time=lead["follow-up 1 time"],
                old_sender_name="Trent",
                old_sender_email=FROM_EMAIL
            )
            send_email(lead["email"], subject, content)
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME
    except Exception as e:
        pass

print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
