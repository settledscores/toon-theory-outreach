import os
import time
import json
import random
import socket
import smtplib
import socks
import dns.resolver

from stem import Signal
from stem.control import Controller

# === CONFIG ===
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051
TOR_PASSWORD = os.getenv("TOR_CONTROL_PASSWORD")  # set this in your shell or .env
INPUT_FILE = "permutations.txt"
OUTPUT_FILE = "verified_emails.json"
SMTP_TIMEOUT = 10
ROTATE_AFTER = 20
SLEEP_BETWEEN = (1, 2)

# === TOR PROXY SETUP ===
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", TOR_SOCKS_PORT)
socket.socket = socks.socksocket

# === TOR IP ROTATION ===
def reset_tor_identity():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as c:
            c.authenticate(password=TOR_PASSWORD)
            c.signal(Signal.NEWNYM)
            print("🔁 New Tor IP identity requested")
    except Exception as e:
        print(f"⚠️ Tor control error: {e}")

# === DNS MX LOOKUP ===
def get_mx(domain):
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return sorted([r.exchange.to_text() for r in answers])[0]
    except:
        return None

# === SMTP VERIFICATION ===
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

# === MAIN ===
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file '{INPUT_FILE}' not found.")
        return

    with open(INPUT_FILE, "r") as f:
        emails = [line.strip() for line in f if line.strip()]

    print(f"🚀 Verifying {len(emails)} emails...\n")

    verified = []
    checked = 0

    for email in emails:
        print(f"🔍 Checking: {email}")
        checked += 1
        if verify_email(email):
            print(f"✅ Valid: {email}\n")
            verified.append(email)
        else:
            print("❌ Invalid\n")

        time.sleep(random.uniform(*SLEEP_BETWEEN))

        if checked % ROTATE_AFTER == 0:
            reset_tor_identity()
            time.sleep(10)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(verified, f, indent=2)

    print("✅ Done.")
    print(f"🧮 Checked: {checked}")
    print(f"📬 Verified: {len(verified)} saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
