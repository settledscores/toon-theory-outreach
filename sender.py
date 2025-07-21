import os
import json
import base64
import random
import imaplib
import email
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from io import BytesIO
from email.generator import BytesGenerator

# === Config ===
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
ZOHO_ACCOUNT_ID = os.environ["ZOHO_ACCOUNT_ID"]
ZOHO_CLIENT_ID = os.environ["ZOHO_CLIENT_ID"]
ZOHO_CLIENT_SECRET = os.environ["ZOHO_CLIENT_SECRET"]
ZOHO_REFRESH_TOKEN = os.environ["ZOHO_REFRESH_TOKEN"]
TIMEZONE = ZoneInfo("Africa/Lagos")

# === Subject Pools ===
INITIAL_SUBJECTS = [
    "Quick idea for your team", "A small idea that might punch above its weight",
    "Trying something different", "What if this helps?", "A curious thought",
    "Saw your site – had a thought", "Trying a new approach here", "Could this click?",
    "This one’s a bit out there", "Small pitch, big upside"
]

FU1_SUBJECTS = [
    "Revisiting my note", "Looping back on this", "Just checking back in",
    "Any thoughts on this?", "Wanted to follow up", "Thought I’d try again"
]

FU2_SUBJECTS = [
    "Giving this one last go", "This might still be worth a look",
    "No worries if not", "Won’t bug you after this", "Couldn’t resist trying again"
]

# === Helpers ===

def refresh_token():
    response = requests.post("https://accounts.zoho.com/oauth/v2/token", data={
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    })
    return response.json()["access_token"]

def encode_email_to_raw(email_message: EmailMessage) -> str:
    buffer = BytesIO()
    gen = BytesGenerator(buffer)
    gen.flatten(email_message)
    raw_bytes = buffer.getvalue()
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

def build_email_message(to, subject, body, message_id=None, in_reply_to=None, references=None):
    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = message_id or make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body)
    return msg

def load_leads():
    with open("leads.ndjson", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def save_leads(leads):
    with open("leads.ndjson", "w", encoding="utf-8") as f:
        for lead in leads:
            f.write(json.dumps(lead) + "\n")

def is_weekend(date):
    return date.weekday() >= 5

def next_weekday(date):
    while is_weekend(date):
        date += timedelta(days=1)
    return date

def get_today():
    return datetime.now(TIMEZONE).date()

def quota_stats(leads):
    today = get_today()
    sent_today = sum(1 for l in leads if l.get("last_sent_date") == str(today))
    recent_initials = sum(1 for l in leads if l.get("stage") == "initial" and l.get("last_sent_date") and
                          (today - datetime.fromisoformat(l["last_sent_date"]).date()).days <= 3)
    backlog_bonus = 20 if recent_initials < 20 else 0
    base_quota = 50
    total_quota = base_quota + backlog_bonus
    return total_quota, sent_today

def pick_next_lead(leads):
    today = get_today()
    eligible = []

    for lead in leads:
        last_sent = datetime.fromisoformat(lead["last_sent_date"]).date() if lead.get("last_sent_date") else None
        stage = lead.get("stage", "initial")

        if stage == "initial" and not last_sent:
            eligible.append((lead, "initial"))
        elif stage == "fu1" and last_sent and (today - last_sent).days >= 3:
            eligible.append((lead, "fu1"))
        elif stage == "fu2" and last_sent and (today - last_sent).days >= 7:
            eligible.append((lead, "fu2"))

    eligible.sort(key=lambda x: {"fu2": 0, "fu1": 1, "initial": 2}[x[1]])
    return eligible[0] if eligible else (None, None)

def send_email_via_zoho(access_token, raw_b64):
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "fromAddress": FROM_EMAIL,
        "accountId": ZOHO_ACCOUNT_ID,
        "mailFormat": "raw",
        "raw": raw_b64
    }
    r = requests.post("https://mail.zoho.com/api/accounts/{}/messages".format(ZOHO_ACCOUNT_ID),
                      headers=headers, json=data)
    return r

# === Main ===

leads = load_leads()
total_quota, sent_today = quota_stats(leads)

print(f"[Quota] Base: 50, Backlogs: {total_quota - 50}, Recent Initials: {sum(1 for l in leads if l.get('stage') == 'initial')}")
print(f"[Quota] Extra: {total_quota - 50}, Total: {total_quota}")
print(f"[Quota] Sent Today: {sent_today}")

if sent_today >= total_quota:
    print("[Exit] Quota reached.")
    exit()

lead, stage = pick_next_lead(leads)
if not lead:
    print("[Exit] No eligible leads.")
    exit()

to_email = lead["email"]
name = lead.get("name", "")
subject = lead.get("subject") if stage != "initial" and "subject" in lead else None

if not subject:
    if stage == "initial":
        subject = random.choice(INITIAL_SUBJECTS)
    elif stage == "fu1":
        subject = random.choice(FU1_SUBJECTS)
    elif stage == "fu2":
        subject = random.choice(FU2_SUBJECTS)

# Example body (replace with your own generator/variant logic)
body = f"Hey {name or 'there'},\n\nJust wanted to share a quick idea—might be useful.\n\nCheers,\nTrent"

# Threading
message_id = lead.get(f"message_id_{stage}")
in_reply_to = lead.get("in-reply-to 1") if stage == "fu1" else lead.get("in-reply-to 2") if stage == "fu2" else None
references = lead.get("references 1") if stage == "fu1" else lead.get("references 2") if stage == "fu2" else None

# Build + encode
msg = build_email_message(to_email, subject, body, message_id=message_id, in_reply_to=in_reply_to, references=references)
raw = encode_email_to_raw(msg)

token = refresh_token()
res = send_email_via_zoho(token, raw)

if res.status_code == 200:
    new_message_id = msg["Message-ID"]
    print(f"[Send] {to_email} | {subject}")
    lead["last_sent_date"] = str(get_today())
    if stage == "initial":
        lead["stage"] = "fu1"
        lead["subject"] = subject
        lead["message_id_initial"] = new_message_id
        lead["in-reply-to 1"] = new_message_id
        lead["references 1"] = new_message_id
    elif stage == "fu1":
        lead["stage"] = "fu2"
        lead["message_id_fu1"] = new_message_id
        lead["in-reply-to 2"] = new_message_id
        lead["references 2"] = f"{lead['references 1']} {new_message_id}"
    elif stage == "fu2":
        lead["stage"] = "done"
        lead["message_id_fu2"] = new_message_id
        lead["in-reply-to 3"] = new_message_id
        lead["references 3"] = f"{lead['references 2']} {new_message_id}"
else:
    print(f"Error:  {to_email}: Zoho send error {res.status_code}: {res.text}")

# Save
save_leads(leads)
print("[Done] Script completed.")
