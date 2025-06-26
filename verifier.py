import socks
import smtplib
import socket
import time
import json
import os
import random
import subprocess
import dns.resolver
from stem import Signal
from stem.control import Controller
from email.utils import parseaddr
from datetime import datetime

# Constants
SOCKS_PROXY = ("127.0.0.1", 9050)
TOR_CONTROL_PORT = 9051
MAX_RETRIES = 3
RETRY_DELAY = 5
SLEEP_BETWEEN_CHECKS = 7  # ~500/hour
EHLO_DOMAIN = "outlook.com"
MX_BYPASS_LIST = [
    "gmail-smtp-in.l.google.com",
    "google.com",
    "outlook.com",
    "protection.outlook.com",
    "hotmail.com",
    "yahoo.com",
    "secureserver.net",
    "zoho.com"
]

# Setup
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/verifier.log"
VERIFIED_FILE = "verified_emails.json"

with open("permutations.txt") as f:
    emails = [line.strip() for line in f if line.strip()]
verified = []

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {message}\n")
    print(message)

def is_tor_alive():
    s = socket.socket()
    try:
        s.settimeout(3)
        s.connect(SOCKS_PROXY)
        return True
    except Exception:
        return False
    finally:
        s.close()

def restart_tor():
    log("⚠️ Restarting Tor...")
    subprocess.run(["sudo", "systemctl", "restart", "tor"], stdout=subprocess.DEVNULL)

def renew_tor_identity():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            log("🔄 Tor identity rotated.")
    except Exception as e:
        log(f"⚠️ Tor control error: {e}")

def get_mx(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return sorted([(r.preference, str(r.exchange).rstrip('.')) for r in answers])
    except Exception as e:
        log(f"❌ MX lookup failed for {domain}: {e}")
        return []

def smtp_check(email):
    domain = email.split("@")[1]
    mx_records = get_mx(domain)
    if not mx_records:
        return False, "no_mx"

    for _, mx in mx_records:
        if any(bypass in mx for bypass in MX_BYPASS_LIST):
            log(f"⚠️ Skipping MX-blocked domain: {email} via {mx}")
            return None, "mx_bypass"

        for attempt in range(MAX_RETRIES):
            try:
                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, *SOCKS_PROXY)
                socket.socket = socks.socksocket

                server = smtplib.SMTP(timeout=10)
                server.connect(mx)
                server.helo(EHLO_DOMAIN)
                server.mail('test@outlook.com')
                code, _ = server.rcpt(email)
                server.quit()

                if code in [250, 251]:
                    return True, "valid"
                else:
                    return False, f"invalid_code_{code}"

            except smtplib.SMTPServerDisconnected:
                log(f"🔁 Retry {email} ({attempt+1}) - Disconnected.")
                time.sleep(RETRY_DELAY)
            except smtplib.SMTPConnectError as e:
                return None, f"connect_error: {e}"
            except Exception as e:
                return None, f"error: {e}"
    return False, "timeout"

log(f"🚀 Verifying {len(emails)} emails...")

for i, email in enumerate(emails):
    if not is_tor_alive():
        log("❌ Tor down. Attempting restart...")
        restart_tor()
        time.sleep(10)

    log(f"🔍 Checking: {email}")
    result, reason = smtp_check(email)

    if result:
        log(f"✅ Valid: {email}")
        verified.append(email)
    elif result is False:
        log(f"❌ Invalid: {email}")
    elif result is None and reason == "mx_bypass":
        log(f"⚠️ Skipped due to major MX block: {email}")
    else:
        log(f"⚠️ Soft fail: {email} — {reason}")
        renew_tor_identity()
        time.sleep(10)

    time.sleep(random.uniform(SLEEP_BETWEEN_CHECKS - 1, SLEEP_BETWEEN_CHECKS + 1))

with open(VERIFIED_FILE, "w") as f:
    json.dump(verified, f, indent=2)

log(f"✅ Done. Verified {len(verified)} / {len(emails)} saved to '{VERIFIED_FILE}'")
