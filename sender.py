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

BASE_START_TIME = time(13, 0)  # 1:00 PM
END_TIME = time(19, 0)         # 7:00 PM
FINAL_END_TIME = time(20, 30)  # 8:30 PM absolute limit

# === Block weekend sends ===
if WEEKDAY >= 5:
    print(f"[Skip] Today is weekend ({TODAY}), no emails should be sent.")
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
    "Explaining complex stuff with simple visuals", "Is your message reaching its full potential?",
    "A story-first idea for {company}", "Cut through mess and set your message free",
    "Idea: use animation to make your message hit harder",
    "This might help supercharge your next big project at {company}",
    "How do you explain what {company} does?"
]

fu1_subjects = [
    "Just Checking In, {name}", "Thought I’d Follow Up, {name}", "Any Thoughts On This, {name}?",
    "Circling Back, {name}", "Sketching Some Ideas For {company}", "A Quick Follow-Up, {name}",
    "Any Interest In This, {name}?", "Here’s That Idea Again, {name}", "Are You Still Open To This, {name}?",
    "Quick Check-In, {name}", "Following Up On That Idea For {company}", "Nudging This Up Your Inbox, {name}",
    "Revisiting, Just In Case You Missed This The Last Time, {name}", "{name}, Got A Sec?",
    "Circling Back To That Idea For {company}", "A Follow-Up From Toon Theory, {name}"
]

fu2_subjects = [
    "Any thoughts on this, {name}?", "Checking back in, {name}", "Quick follow-up, {name}",
    "Still curious if this helps", "Wondering if this sparked anything", "Visual storytelling, still on the table?",
    "A quick nudge your way", "Happy to mock something up", "Short reminder, {name}",
    "Just revisiting this idea", "Whiteboard sketch still an option?", "No pressure, just following up",
    "Back with another nudge", "A final nudge, {name}", "Hoping this reached you",
    "Revisiting that animation idea", "Let me know if now's better", "Still worth exploring?",
    "Quick question on our last email", "Still around if helpful", "Do you want me to close this out?",
    "Open to creative pitches?", "Just in case it got buried"
]

random.shuffle(initial_subjects)
random.shuffle(fu1_subjects)
random.shuffle(fu2_subjects)

def next_subject(pool, **kwargs):
    if not pool:
        return None
    template = pool.pop(0)
    pool.append(template)
    return template.format(**kwargs)

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

def send_email(to, subject, content, in_reply_to=None):
    print(f"[Send] {to} | {subject}")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg.set_content(content)
    msg_id = make_msgid(domain=FROM_EMAIL.split("@")[-1])[1:-1]
    msg["Message-ID"] = f"<{msg_id}>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, from_addr=FROM_EMAIL)
    return msg_id

def check_replies(message_ids):
    seen = set()
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as imap:
        imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        for folder in ["INBOX", "SPAM", "Junk", "[Gmail]/Spam"]:
            try:
                imap.select(folder)
                typ, data = imap.search(None, "ALL")
                for num in data[0].split():
                    typ, msg_data = imap.fetch(num, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    headers = (msg.get("In-Reply-To") or "") + (msg.get("References") or "")
                    for mid in message_ids:
                        if f"<{mid}>" in headers:
                            seen.add(mid)
            except: continue
    return seen

# === Load and normalize leads ===
leads = read_multiline_ndjson(LEADS_FILE)
for lead in leads:
    for field in [
        "email", "email 1", "email 2", "email 3", "business name", "first name",
        "message id", "message id 2", "message id 3", "subject",
        "initial date", "follow-up 1 date", "follow-up 2 date",
        "initial time", "follow-up 1 time", "follow-up 2 time", "reply"
    ]:
        lead.setdefault(field, "")

# === Update replies ===
all_ids = [l["message id"] for l in leads if l["message id"]] + \
          [l["message id 2"] for l in leads if l["message id 2"]] + \
          [l["message id 3"] for l in leads if l["message id 3"]]
replied = check_replies(all_ids)
for lead in leads:
    if lead["reply"] == "no reply":
        if lead["message id 3"] in replied:
            lead["reply"] = "after FU2"
        elif lead["message id 2"] in replied:
            lead["reply"] = "after FU1"
        elif lead["message id"] in replied:
            lead["reply"] = "after initial"
    elif not lead["reply"]:
        lead["reply"] = "no reply"

# === Eligibility and Quota ===
def can_send_initial(lead):
    return not lead["initial date"] and lead.get("email") and lead.get("email 1")

def can_send_followup(lead, step):
    if lead["reply"] != "no reply" or not lead.get("email"):
        return False
    if step == 2:
        prev_key, msg_key, curr_key, content_key = "initial date", "message id", "follow-up 1 date", "email 2"
    elif step == 3:
        prev_key, msg_key, curr_key, content_key = "follow-up 1 date", "message id 2", "follow-up 2 date", "email 3"
    else:
        return False
    if not (lead[prev_key] and lead[msg_key] and not lead[curr_key] and lead.get(content_key)):
        return False
    due_date = datetime.strptime(lead[prev_key], "%Y-%m-%d").date() + timedelta(days=(3 if step == 2 else 4))
    while due_date.weekday() >= 5:
        due_date += timedelta(days=1)
    return TODAY >= due_date

def backlog_count(leads):
    return sum(1 for l in leads if can_send_followup(l, 2) or can_send_followup(l, 3))

def initials_sent_in_last_days(n):
    count = 0
    day = TODAY - timedelta(days=1)
    checked = 0
    while checked < n:
        if day.weekday() < 5:
            if any(l.get("initial date") == day.isoformat() for l in leads):
                count += sum(1 for l in leads if l.get("initial date") == day.isoformat())
            checked += 1
        day -= timedelta(days=1)
    return count

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

# === Dynamic Eligibility Window ===
total_minutes_needed = DAILY_QUOTA * 7
ideal_start = datetime.combine(TODAY, BASE_START_TIME) - timedelta(minutes=total_minutes_needed)
ideal_end = datetime.combine(TODAY, END_TIME) + timedelta(minutes=(DAILY_QUOTA - BASE_QUOTA) * 7)

window_start = ideal_start.time()
window_end = min(ideal_end.time(), FINAL_END_TIME)

if not window_start <= NOW.time() <= window_end:
    print(f"[Skip] Outside dynamic window ({NOW.time()} WAT), allowed {window_start}–{window_end}")
    exit(0)

# === Send Queue ===
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

print(f"[Quota] Base: {BASE_QUOTA}, Backlogs: {backlogs}, Recent Initials: {recent_initials}")
print(f"[Quota] Extra: {extra_quota}, Total: {DAILY_QUOTA}")
print(f"[Quota] Sent Today: {sent_today}")
print(f"[Process] {len(queue)} message(s) to send...")

# === Send Email ===
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
            subject = f"Re: {lead['subject']}" if lead["subject"] else next_subject(fu1_subjects, name=lead["first name"], company=lead["business name"])
            msgid = send_email(lead["email"], subject, lead["email 2"], f"<{lead['message id']}>")
            lead["message id 2"] = msgid
            lead["follow-up 1 date"] = TODAY.isoformat()
            lead["follow-up 1 time"] = NOW_TIME
        elif kind == "fu2":
            subject = f"Re: {lead['subject']}" if lead["subject"] else next_subject(fu2_subjects, name=lead["first name"], company=lead["business name"])
            msgid = send_email(lead["email"], subject, lead["email 3"], f"<{lead['message id 2']}>")
            lead["message id 3"] = msgid
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME
    except Exception as e:
        print(f"[Error] {lead.get('email', 'UNKNOWN')}: {e}")

print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
