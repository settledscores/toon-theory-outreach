import json
import smtplib
import imaplib
import email
import os
import random
import re
from datetime import datetime, timedelta, time
from email.message import EmailMessage
from zoneinfo import ZoneInfo

# === Config ===
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", EMAIL_ADDRESS)
IMAP_SERVER = os.environ["IMAP_SERVER"]
IMAP_PORT = int(os.environ["IMAP_PORT"])
SMTP_SERVER = "smtppro.zoho.com"
SMTP_PORT = 465

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
    print("[Skipped] Weekend detected — exiting.")
    exit(0)

# === Subjects ===
initial_subjects = [
    # original + 15 new to double pool
    "Ever seen a pitch drawn out?", "You’ve probably never gotten an email like this",
    "This might sound odd, but useful", "Not sure if this will land, but here goes",
    "You might like what I’ve been sketching", "This idea’s been stuck in my head",
    "Bet you haven’t tried this approach yet", "What if your next pitch was drawn?",
    "This has worked weirdly well for others", "A small idea that might punch above its weight",
    "Something about {company} got me thinking", "Is this a weird idea? Maybe.", "Is this worth trying? Probably.",
    "Thought of you while doodling", "This one might be a stretch, but could work",
    "Felt like this might be your kind of thing", "Kind of random, but hear me out",
    "If you're up for an odd idea", "Not a pitch, just something I had to share",
    "This one’s a bit out there", "Saw what you’re doing, had to send this",
    "Wanna try something weird?", "Ever tried sketching your message?",
    "Quick thought: could sketches help?", "Something visual that might work for {company}",
    "This stuck in my head after seeing {company}", "Quick idea you probably haven’t seen before",
    "Hope this doesn’t sound too off", "Could this work for your pitch?",
    "Bit of an odd angle, but may click", "Does this feel off-brand or on-point?",
    "Just playing with this angle", "This made me think of {company}",
]
random.shuffle(initial_subjects)

# === Signature Management ===
SIGNATURES = [
    "Warmly,\nTrent — Toon Theory\ntoontheory.com\nWhiteboard videos your customers will actually remember.",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com\nTrusted by consultants, coaches, and businesses who care about clarity.",
    "Cheers,\nTrent — Toon Theory\nhttps://toontheory.com\nExplainer videos made to convert, not just impress.",
    "Take care,\nTrent — Toon Theory\nwww.toontheory.com\nThe explainer video partner for thoughtful, service-based brands.",
    "Sincerely,\nTrent — Founder, Toon Theory\ntoontheory.com\nHelping you teach, pitch, and persuade in under two minutes.",
    "Best wishes,\nTrent — Toon Theory\nwww.toontheory.com\nAnimation for experts who need to sound less 'expert-y'.",
    "Kind regards,\nTrent — Founder, Toon Theory\nhttps://www.toontheory.com\nExplainers that turn confusion into conversion.",
    "Respectfully,\nTrent — Toon Theory\nhttps://toontheory.com\nTrusted by consultants, coaches, and businesses who care about clarity.",
    "Warm regards,\nTrent — Founder @ Toon Theory\nwww.toontheory.com\nExplainer videos made to convert, not just impress.",
    "Regards,\nTrent — Toon Theory\nhttps://www.toontheory.com\nThe explainer video partner for thoughtful, service-based brands.",
    "With gratitude,\nTrent — Toon Theory\nwww.toontheory.com\nHelping you teach, pitch, and persuade in under two minutes.",
    "Yours truly,\nTrent — Founder, Toon Theory\ntoontheory.com\nAnimation for experts who need to sound less 'expert-y'.",
    "Faithfully,\nTrent — Toon Theory\nwww.toontheory.com\nExplainers that turn confusion into conversion.",
    "Thanks,\nTrent — Toon Theory\nhttps://www.toontheory.com\nExplainer videos made to convert, not just impress."
]
_signature_pattern = re.compile("|".join(re.escape(sig) for sig in SIGNATURES), flags=re.MULTILINE)
def strip_signature(text): return _signature_pattern.sub("", text).strip()

# === Utility Functions ===
def next_subject(pool, **kwargs):
    if not pool: return None
    template = pool.pop(0)
    pool.append(template)
    return template.format(**kwargs)

def quote_previous_message(new_text, old_text, old_date, old_time, old_sender_name, old_sender_email):
    old_dt = datetime.strptime(f"{old_date} {old_time}", "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)
    formatted_date = old_dt.strftime("%A, %b %d, %Y")
    header_line = f"--- On {formatted_date}, {old_sender_name} <{old_sender_email}> wrote ---"
    separator = "\n" + ("─" * 72) + "\n"
    quoted = "\n".join(["> " + line for line in old_text.strip().splitlines()])
    return f"{new_text}{separator}{header_line}\n{quoted}"

def weekday_offset(start_date, days):
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current

def can_send_initial(lead):
    return not lead["initial date"] and lead.get("email") and lead.get("email 1")

def can_send_followup(lead, step):
    if lead["reply"] != "no reply" or not lead.get("email"):
        return False
    if step == 2:
        if not lead["initial date"] or lead["follow-up 1 date"] or not lead.get("email 2"):
            return False
        eligible_date = weekday_offset(datetime.strptime(lead["initial date"], "%Y-%m-%d").date(), 3)
        return TODAY >= eligible_date
    elif step == 3:
        if not lead["follow-up 1 date"] or lead["follow-up 2 date"] or not lead.get("email 3"):
            return False
        eligible_date = weekday_offset(datetime.strptime(lead["follow-up 1 date"], "%Y-%m-%d").date(), 4)
        return TODAY >= eligible_date
    return False

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

# === Load Leads ===
leads = read_multiline_ndjson(LEADS_FILE)
for lead in leads:
    if is_minimal_url_only(lead):
        continue  # ⛔ Skip untouched

    for field in [
        "email", "email 1", "email 2", "email 3", "business name", "first name", "subject",
        "initial date", "follow-up 1 date", "follow-up 2 date",
        "initial time", "follow-up 1 time", "follow-up 2 time", "reply"
    ]:
        lead.setdefault(field, "")
    if not lead["reply"]:
        lead["reply"] = "no reply"

def is_minimal_url_only(lead):
    """Return True if the lead only contains 'website url'."""
    return (
        list(lead.keys()) == ["website url"]
        or (
            "website url" in lead
            and all(
                (k == "website url" or not str(v).strip())
                for k, v in lead.items()
            )
        )
)

# === Quota Logic ===
def backlog_count(leads): return sum(1 for l in leads if can_send_followup(l, 2) or can_send_followup(l, 3))
def initials_sent_in_last_days(n):
    count, day, checked = 0, TODAY - timedelta(days=1), 0
    while checked < n:
        if day.weekday() < 5:
            count += sum(1 for l in leads if l.get("initial date") == day.isoformat())
            checked += 1
        day -= timedelta(days=1)
    return count

BASE_QUOTA = 50
backlogs = backlog_count(leads)
recent_initials = initials_sent_in_last_days(3)
extra_quota = min(20, backlogs)
if recent_initials < 20: extra_quota += 20
DAILY_QUOTA = BASE_QUOTA + extra_quota
sent_today = sum(1 for l in leads if TODAY.isoformat() in [l.get("initial date"), l.get("follow-up 1 date"), l.get("follow-up 2 date")])

print(f"[Quota] Base: {BASE_QUOTA}, Backlogs: {backlogs}, Recent Initials: {recent_initials}")
print(f"[Quota] Extra: {extra_quota}, Total: {DAILY_QUOTA}")
print(f"[Quota] Sent Today: {sent_today}")

# === Time Window ===
total_minutes_needed = DAILY_QUOTA * 7
ideal_start = datetime.combine(TODAY, BASE_START_TIME) - timedelta(minutes=total_minutes_needed)
ideal_end = datetime.combine(TODAY, END_TIME) + timedelta(minutes=(DAILY_QUOTA - BASE_QUOTA) * 7)
window_start = ideal_start.time()
window_end = min(ideal_end.time(), FINAL_END_TIME)
if not window_start <= NOW.time() <= window_end:
    exit(0)

# === Message Selection & Send ===
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
    if queue: break

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
            content = quote_previous_message(
                new_text=lead["email 2"],
                old_text=strip_signature(lead["email 1"]),
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

            initial_quoted = quote_previous_message(
                new_text=strip_signature(lead["email 1"]),
                old_text="",
                old_date=lead["initial date"],
                old_time=lead["initial time"],
                old_sender_name="Trent",
                old_sender_email=FROM_EMAIL
            ).strip()

            fu1_quoted = quote_previous_message(
                new_text=strip_signature(lead["email 2"]),
                old_text=initial_quoted,
                old_date=lead["follow-up 1 date"],
                old_time=lead["follow-up 1 time"],
                old_sender_name="Trent",
                old_sender_email=FROM_EMAIL
            )

            content = quote_previous_message(
                new_text=lead["email 3"],
                old_text=fu1_quoted,
                old_date=TODAY.isoformat(),
                old_time=NOW_TIME,
                old_sender_name="Trent",
                old_sender_email=FROM_EMAIL
            )

            send_email(lead["email"], subject, content)
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME

    except Exception as e:
        print(f"[Error] Failed to send {kind} to {lead.get('email')}: {e}")

# === Save File ===
print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
