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

# === ENVIRONMENT VARIABLES ===
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
TOR_PASSWORD = os.getenv("TOR_CONTROL_PASSWORD")

# === SETTINGS ===
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051
SMTP_TIMEOUT = 10
ROTATE_AFTER = 20
SLEEP_BETWEEN = (1, 2)
PAGE_SIZE = 100

# === SOCKS5 PROXY SETUP FOR TOR ===
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", TOR_SOCKS_PORT)
socket.socket = socks.socksocket

# === ROTATE TOR IDENTITY ===
def reset_tor_identity():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as c:
            c.authenticate(password=TOR_PASSWORD)
            c.signal(Signal.NEWNYM)
            print("🔁 IP rotated via Tor\n")
    except Exception as e:
        print(f"⚠️ Tor IP rotation failed: {e}")

# === GET RECORDS FROM AIRTABLE ===
def get_airtable_records(offset=None):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{quote(SCRAPER_TABLE_NAME)}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = [
        ("pageSize", PAGE_SIZE),
        ("fields[]", "Email Permutations")
    ]
    if offset:
        params.append(("offset", offset))

    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        print(f"❌ Airtable API Error {response.status_code}")
        print(f"↪️ URL: {url}")
        print(f"↪️ Response: {response.text}")
        response.raise_for_status()

    return response.json()

# === UPDATE VERIFIED RESULT TO AIRTABLE ===
def update_verified_email(record_id, verified_email):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{quote(SCRAPER_TABLE_NAME)}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"fields": {"Verified Permutation": verified_email}}
    response = requests.patch(url, headers=headers, json=data)
    if not response.ok:
        print(f"❌ Airtable PATCH Error {response.status_code}")
        print(f"↪️ URL: {url}")
        print(f"↪️ Response: {response.text}")
        response.raise_for_status()

# === GET MX RECORD FOR DOMAIN ===
def get_mx(domain):
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return sorted([r.exchange.to_text() for r in answers])[0]
    except:
        return None

# === VERIFY EMAIL OVER SMTP ===
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

# === MAIN VERIFICATION LOOP ===
def main():
    print("🚀 Starting email verification with Tor\n")
    total_checked = 0
    total_verified = 0
    total_records = 0
    offset = None

    while True:
        batch = get_airtable_records(offset)
        records = batch.get("records", [])

        if not records:
            break

        for record in records:
            total_records += 1
            record_id = record["id"]
            fields = record.get("fields", {})
            perms = fields.get("Email Permutations", "")

            if not perms:
                continue

            emails = [e.strip() for e in perms.split(",") if e.strip()]
            print(f"🔍 [{total_records}] {len(emails)} permutations")

            for email in emails:
                print(f"   ➤ Trying: {email}")
                total_checked += 1
                if verify_email(email):
                    print(f"   ✅ Verified: {email}\n")
                    update_verified_email(record_id, email)
                    total_verified += 1
                    break
                else:
                    print("   ❌ Invalid")

                time.sleep(random.uniform(*SLEEP_BETWEEN))

                if total_checked % ROTATE_AFTER == 0:
                    reset_tor_identity()
                    time.sleep(10)

        offset = batch.get("offset")
        if not offset:
            break

    print("\n🎯 Done")
    print(f"🧮 Records processed:  {total_records}")
    print(f"📬 Emails verified:    {total_verified}")
    print(f"📤 Permutations tried: {total_checked}")

if __name__ == "__main__":
    main()
