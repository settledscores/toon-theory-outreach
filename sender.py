import os
import json
import smtplib
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re
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

# === Helpers for NDJSON ===
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

# === IMAP scanning utilities ===
IMAP_FOLDERS = ["INBOX", "[Gmail]/Spam", "SPAM", "Spam", "Junk"]

def _safe_decode_header(value):
    if value is None:
        return ""
    parts = decode_header(value)
    out = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                out += part.decode(enc or "utf-8", errors="ignore")
            except:
                out += part.decode(errors="ignore")
        else:
            out += part
    return out

def _extract_body_text(msg):
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get("Content-Disposition", ""))
                if ctype == "text/plain" and "attachment" not in disp:
                    try:
                        body += part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                    except:
                        body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            try:
                body += msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
            except:
                body += msg.get_payload(decode=True).decode(errors="ignore")
    except Exception:
        # last resort: try raw payload decode
        try:
            raw = msg.as_bytes()
            body += raw.decode(errors="ignore")
        except:
            pass
    # If only HTML present, strip tags lightly
    if "<html" in body.lower() and not re.search(r"\w{3,}", body):
        body = re.sub(r"<[^>]+>", "", body)
    return body

def _parse_msg_datetime(msg):
    date_hdr = msg.get("Date")
    if not date_hdr:
        return None
    try:
        dt = parsedate_to_datetime(date_hdr)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TIMEZONE)
        return dt.astimezone(TIMEZONE)
    except Exception:
        return None

def detect_reply_status(leads):
    """
    Scans IMAP folders and marks leads with 'reply' if we detect a reply or bounce.
    It compares message date to each lead's last send time to decide whether the reply occurred after
    initial / FU1 / FU2.
    """
    print("[IMAP] Scanning mailbox for replies/bounces...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    except Exception as e:
        print(f"[IMAP] Connection error: {e}")
        return

    # Normalize leads index by email for quick lookup
    lead_map = {}
    for lead in leads:
        email_key = str(lead.get("email", "")).strip().lower()
        if email_key:
            lead_map.setdefault(email_key, []).append(lead)

    # Precompute lead send datetimes (tz-aware) for comparisons
    def lead_send_dt(lead, date_field, time_field):
        d = str(lead.get(date_field, "")).strip()
        t = str(lead.get(time_field, "")).strip()
        if not d or not t:
            return None
        try:
            return datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)
        except:
            return None

    # Scan folders
    for folder in IMAP_FOLDERS:
        try:
            mail.select(folder, readonly=True)
        except Exception:
            continue  # skip folders that don't exist / can't be opened

        # We'll search recent messages to reduce load — since last 30 days
        since_date = (TODAY - timedelta(days=30)).strftime("%d-%b-%Y")
        try:
            status, data = mail.search(None, f'(SINCE "{since_date}")')
        except Exception:
            try:
                status, data = mail.search(None, 'ALL')
            except Exception:
                continue

        if status != "OK":
            continue

        for num in data[0].split():
            try:
                res, msg_data = mail.fetch(num, "(RFC822)")
                if res != "OK" or not msg_data:
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
            except Exception:
                continue

            from_addr = email.utils.parseaddr(msg.get("From", ""))[1].lower()
            subject = _safe_decode_header(msg.get("Subject"))
            body = _extract_body_text(msg)
            msg_dt = _parse_msg_datetime(msg) or datetime.now(TIMEZONE)

            # Quick bounce-from check
            from_is_bounce_source = ("mailer-daemon" in from_addr) or ("postmaster" in from_addr) or ("<> " in from_addr)

            # For each lead email present in either from, subject, or body, mark accordingly
            # Note: this is O(m*n) but keeps behavior exact to your requirement
            for lead_email, lead_list in lead_map.items():
                if not lead_email:
                    continue
                matched = False
                # check from
                if lead_email in from_addr:
                    matched = True
                # check subject
                elif lead_email in subject.lower():
                    matched = True
                # check body
                elif lead_email in (body or "").lower():
                    matched = True

                if not matched:
                    # if bounce-like from and lead email in body -> bounce
                    if from_is_bounce_source and re.search(re.escape(lead_email), body or "", re.IGNORECASE):
                        matched = True
                        bounce_detected = True
                    else:
                        bounce_detected = False

                if matched:
                    for lead in lead_list:
                        # compute lead send datetimes
                        initial_dt = lead_send_dt(lead, "initial date", "initial time")
                        fu1_dt = lead_send_dt(lead, "follow-up 1 date", "follow-up 1 time")
                        fu2_dt = lead_send_dt(lead, "follow-up 2 date", "follow-up 2 time")

                        # bounce detection determination
                        is_bounce = False
                        if from_is_bounce_source and re.search(re.escape(lead_email), body or "", re.IGNORECASE):
                            is_bounce = True
                        # also consider bounce if subject contains common bounce phrases
                        if re.search(r"undeliver|delivery failure|delivery status notification|failure notice|returned mail|delivery failed", subject, re.IGNORECASE):
                            if re.search(re.escape(lead_email), body or "", re.IGNORECASE):
                                is_bounce = True

                        if is_bounce:
                            lead["reply"] = f"bounced ({folder})"
                            print(f"[IMAP] Bounce for {lead_email} found in {folder} (msg {num.decode() if isinstance(num, bytes) else num}).")
                            continue

                        # Otherwise it's a human reply or mention
                        # Determine which send it came after (FU2 > FU1 > initial > before initial)
                        # If the message datetime is after the respective send dt, mark accordingly
                        if fu2_dt and msg_dt >= fu2_dt:
                            lead["reply"] = "after FU2"
                            print(f"[IMAP] Reply for {lead_email} after FU2 (folder {folder}).")
                        elif fu1_dt and msg_dt >= fu1_dt:
                            lead["reply"] = "after FU1"
                            print(f"[IMAP] Reply for {lead_email} after FU1 (folder {folder}).")
                        elif initial_dt and msg_dt >= initial_dt:
                            lead["reply"] = "after initial"
                            print(f"[IMAP] Reply for {lead_email} after initial (folder {folder}).")
                        else:
                            # Reply predates any recorded sends — still mark to avoid sending
                            lead["reply"] = "reply (pre-existing)"
                            print(f"[IMAP] Pre-existing reply for {lead_email} found in {folder}; skipping sends.")

    try:
        mail.logout()
    except Exception:
        pass

# Helper: per-lead focused check (used right before each send to be extra-safe)
def has_recent_reply_or_bounce(lead, since_dt):
    """
    Check mailbox for replies/bounces for a single lead since `since_dt`.
    since_dt should be a timezone-aware datetime in TIMEZONE (or None).
    Returns (found: bool, reason: str).
    """
    lead_email = str(lead.get("email", "")).strip().lower()
    if not lead_email:
        return False, "no email"

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    except Exception as e:
        print(f"[IMAP] per-lead connect error: {e}")
        return False, "imap error"

    # Use SINCE search using date only if since_dt provided
    since_str = None
    if isinstance(since_dt, datetime):
        since_str = since_dt.strftime("%d-%b-%Y")
    else:
        since_str = (TODAY - timedelta(days=30)).strftime("%d-%b-%Y")

    for folder in IMAP_FOLDERS:
        try:
            mail.select(folder, readonly=True)
        except Exception:
            continue
        try:
            status, data = mail.search(None, f'(SINCE "{since_str}")')
        except Exception:
            try:
                status, data = mail.search(None, 'ALL')
            except Exception:
                continue

        if status != "OK":
            continue

        for num in data[0].split():
            try:
                res, msg_data = mail.fetch(num, "(RFC822)")
                if res != "OK" or not msg_data:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
            except Exception:
                continue

            from_addr = email.utils.parseaddr(msg.get("From", ""))[1].lower()
            subject = _safe_decode_header(msg.get("Subject"))
            body = _extract_body_text(msg)
            msg_dt = _parse_msg_datetime(msg) or datetime.now(TIMEZONE)

            # direct reply
            if lead_email in from_addr or lead_email in subject.lower() or re.search(re.escape(lead_email), body or "", re.IGNORECASE):
                # bounce heuristics
                if ("mailer-daemon" in from_addr) or ("postmaster" in from_addr) or re.search(r"undeliver|delivery failure|returned mail", subject, re.IGNORECASE):
                    if re.search(re.escape(lead_email), body or "", re.IGNORECASE):
                        try:
                            mail.logout()
                        except:
                            pass
                        return True, f"bounced ({folder})"
                try:
                    mail.logout()
                except:
                    pass
                return True, f"reply in {folder}"

    try:
        mail.logout()
    except:
        pass
    return False, ""

# === Send rules ===
def can_send_initial(lead):
    return not lead.get("initial date") and lead.get("email") and lead.get("email 1")

def can_send_followup(lead, step):
    """
    Determine if a follow-up can be sent.
    step = 2 → FU1
    step = 3 → FU2
    Note: this function assumes detect_reply_status() has been run earlier,
    but still checks the 'reply' field.
    """

    def is_empty(value):
        return value is None or str(value).strip() == ""

    # Skip if there's any known reply
    if str(lead.get("reply", "no reply")).strip().lower() != "no reply":
        print(f"[SKIP FU{step}] Lead {lead.get('email')} already replied ({lead.get('reply')}).")
        return False

    # Skip if main email missing
    if is_empty(lead.get("email")):
        print(f"[SKIP FU{step}] Lead missing primary email.")
        return False

    try:
        if step == 2:  # FU1 rules
            if is_empty(lead.get("initial date")):
                print(f"[SKIP FU1] Missing initial date for {lead.get('email')}.")
                return False
            if not is_empty(lead.get("follow-up 1 date")):
                print(f"[SKIP FU1] Already sent FU1 to {lead.get('email')}.")
                return False
            if is_empty(lead.get("email 2")):
                print(f"[SKIP FU1] Missing 'email 2' for {lead.get('email')}.")
                return False

            last_dt = datetime.strptime(
                f"{lead['initial date']} {lead['initial time']}", "%Y-%m-%d %H:%M"
            ).replace(tzinfo=TIMEZONE)
            if NOW < last_dt + timedelta(minutes=5):
                print(f"[SKIP FU1] Too early for FU1 to {lead.get('email')}.")
                return False
            return True

        elif step == 3:  # FU2 rules
            if is_empty(lead.get("follow-up 1 date")):
                print(f"[SKIP FU2] Missing FU1 date for {lead.get('email')}.")
                return False
            if not is_empty(lead.get("follow-up 2 date")):
                print(f"[SKIP FU2] Already sent FU2 to {lead.get('email')}.")
                return False
            if is_empty(lead.get("email 3")):
                print(f"[SKIP FU2] Missing 'email 3' for {lead.get('email')}.")
                return False

            last_dt = datetime.strptime(
                f"{lead['follow-up 1 date']} {lead['follow-up 1 time']}", "%Y-%m-%d %H:%M"
            ).replace(tzinfo=TIMEZONE)
            if NOW < last_dt + timedelta(minutes=5):
                print(f"[SKIP FU2] Too early for FU2 to {lead.get('email')}.")
                return False
            return True

    except Exception as e:
        print(f"[ERROR FU{step}] {lead.get('email')}: {e}")
        return False

    return False

# === Email send function ===
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

# Run a bulk IMAP scan to update reply/bounce status before we pick a queue
detect_reply_status(leads)

# === Quota logic (unchanged) ===
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

# === Build single-send queue (one lead at a time) ===
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

# === Send loop with per-lead IMAP check immediately before send ===
for kind, lead in queue:
    try:
        # Determine since_dt for per-lead check:
        if kind == "initial":
            # For initial sends, check the last 30 days for inbound messages from the lead
            since_dt = NOW - timedelta(days=30)
        elif kind == "fu1":
            # FU1 should check since the initial send time
            try:
                since_dt = datetime.strptime(f"{lead['initial date']} {lead['initial time']}", "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)
            except:
                since_dt = NOW - timedelta(days=30)
        elif kind == "fu2":
            try:
                since_dt = datetime.strptime(f"{lead['follow-up 1 date']} {lead['follow-up 1 time']}", "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)
            except:
                since_dt = NOW - timedelta(days=30)
        else:
            since_dt = NOW - timedelta(days=30)

        # Quick per-lead mailbox check to be extra-safe (catches replies that arrived after the bulk scan)
        found, reason = has_recent_reply_or_bounce(lead, since_dt)
        if found:
            lead["reply"] = reason
            print(f"[SKIP BEFORE SEND] {lead.get('email')} — {reason}")
            continue

        # Proceed to send according to kind
        if kind == "initial":
            subject = next_subject(initial_subjects, company=lead["business name"])
            send_email(lead["email"], subject, lead["email 1"])
            lead["subject"] = subject
            lead["initial date"] = TODAY.isoformat()
            lead["initial time"] = NOW_TIME
            print(f"[SENT initial] {lead.get('email')} - subject: {subject}")

        elif kind == "fu1":
            subject = f"Re: {lead['subject']}" if lead["subject"] else "Just checking in"
            send_email(lead["email"], subject, lead["email 2"])
            lead["follow-up 1 date"] = TODAY.isoformat()
            lead["follow-up 1 time"] = NOW_TIME
            print(f"[SENT FU1] {lead.get('email')} - subject: {subject}")

        elif kind == "fu2":
            subject = f"Re: {lead['subject']}" if lead["subject"] else "Just circling back"
            send_email(lead["email"], subject, lead["email 3"])
            lead["follow-up 2 date"] = TODAY.isoformat()
            lead["follow-up 2 time"] = NOW_TIME
            print(f"[SENT FU2] {lead.get('email')} - subject: {subject}")

    except Exception as e:
        print(f"[Error] Failed to send {kind} to {lead.get('email')}: {e}")

# === Save updated leads file (with reply flags and timestamps) ===
print("[Save] Writing updated leads file...")
write_multiline_ndjson(LEADS_FILE, leads)
print("[Done] Script completed.")
