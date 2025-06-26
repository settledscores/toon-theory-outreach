import os
import time
import random
import socket
import smtplib
import socks
import requests
import dns.resolver

from urllib.parse import quote
from stem import Signal
from stem.control import Controller

# === Environment Variables ===
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
TOR_PASSWORD = os.getenv("TOR_CONTROL_PASSWORD")

# === Tor & SMTP Settings ===
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051
SMTP_TIMEOUT = 10
ROTATE_AFTER = 20
SLEEP_BETWEEN = (1, 2)
PAGE_SIZE = 100

# === Use Tor for all outbound SMTP ===
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", TOR_SOCKS_PORT)
socket.socket = socks.socksocket

# === Reset Tor IP ===
def reset_tor_identity():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
            print("🔁 Tor identity rotated.")
    except Exception as e:
        print(f"⚠️ Failed to rotate Tor identity: {e}")

# === Get Airtable Records ===
def get_airtable_records(offset=None):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{quote(SCRAPER_TABLE_NAME)}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "pageSize": PAGE_SIZE,
        "fields[]": ["Name", "Domain", "Email Permutations"]
    }
    if offset:
        params["offset"] = offset
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# === Update Airtable Record ===
def update_verified_email(record_id, verified_email):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{quote(SCRAPER_TABLE_NAME)}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"fields": {"Verified Permutation": verified_email}}
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()

# === Get MX Record ===
def get_mx(domain):
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return sorted([r.exchange.to_text() for r in answers])[0]
    except:
        return None

# === SMTP Verify ===
def verify_email(email):
    domain = email.split("@")[-1]
    mx = get_mx(domain)
    if not mx:
        return False
    try:
        server = smtplib.SMTP(mx, 25, timeout=SMTP_TIMEOUT)
        server.helo("example.com")
        server.mail("test@example.com")
        code, _ = server.rcpt(email)
        server.quit()
        return code in [250, 251]
    except:
        return False

# === Main Execution ===
def main():
    print("🚀 Starting email verifier with Tor IP rotation...\n")
    total = 0
    offset = None

    while True:
        batch = get_airtable_records(offset)
        records = batch.get("records", [])

        for record in records:
            record_id = record["id"]
            fields = record.get("fields", {})
            name = fields.get("Name", "")
            domain = fields.get("Domain", "")
            perms = fields.get("Email Permutations", "")

            if not perms or not domain:
                continue

            emails = [e.strip() for e in perms.split(",") if e.strip()]
            print(f"👤 {name} ({domain}) → {len(emails)} guesses")

            for email in emails:
                print(f"🔎 {email}")
                total += 1
                if verify_email(email):
                    print(f"✅ Verified: {email}")
                    update_verified_email(record_id, email)
                    break
                else:
                    print("❌ Invalid")

                time.sleep(random.uniform(*SLEEP_BETWEEN))

                if total % ROTATE_AFTER == 0:
                    reset_tor_identity()
                    time.sleep(10)

        offset = batch.get("offset")
        if not offset:
            break

    print("\n🎯 Verification complete.")

if __name__ == "__main__":
    main()
