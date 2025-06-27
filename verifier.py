import dns.resolver
import smtplib
import socket
import socks
import time
import random
import logging
from email.utils import parseaddr
from pathlib import Path

# Static list of Webshare proxies
PROXIES = [
    {"host": "198.23.239.134", "port": 6540, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "207.244.217.165", "port": 6712, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "107.172.163.27", "port": 6543, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "23.94.138.75", "port": 6349, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "216.10.27.159", "port": 6837, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "136.0.207.84", "port": 6661, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "64.64.118.149", "port": 6732, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "142.147.128.93", "port": 6593, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "104.239.105.125", "port": 6655, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
    {"host": "173.0.9.70", "port": 5653, "user": "grkwzeug", "pass": "p87xh2t5n1o9"},
]

# Email verification logic
RETRY_CODES = [421, 450, 451, 452, 550]
MAX_RETRIES = 3
SMTP_TIMEOUT = 10
LOG_LEVEL = logging.INFO

# Set up logger
logging.basicConfig(level=LOG_LEVEL, format='[%(asctime)s] %(message)s')


def get_random_proxy():
    return random.choice(PROXIES)


def configure_proxy(proxy):
    socks.setdefaultproxy(
        socks.SOCKS5,
        proxy["host"],
        proxy["port"],
        True,
        username=proxy["user"],
        password=proxy["pass"]
    )
    socket.socket = socks.socksocket


def get_mx_record(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        records = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in answers])
        return records[0][1] if records else None
    except Exception as e:
        logging.warning(f"❌ MX lookup failed for domain {domain}: {e}")
        return None


def smtp_check(email, mx_host, proxy):
    try:
        configure_proxy(proxy)
        server = smtplib.SMTP(mx_host, 25, timeout=SMTP_TIMEOUT)
        server.helo()
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()
        return code, message.decode() if isinstance(message, bytes) else str(message)
    except Exception as e:
        return None, str(e)


def verify_email(email):
    name, addr = parseaddr(email.strip())
    if '@' not in addr:
        return email, 'invalid', 'Not a valid email address'
    
    domain = addr.split('@')[-1]
    mx_host = get_mx_record(domain)
    if not mx_host:
        return email, 'invalid', 'No MX record found'

    for attempt in range(1, MAX_RETRIES + 1):
        proxy = get_random_proxy()
        code, msg = smtp_check(addr, mx_host, proxy)
        if code is None:
            logging.warning(f"⚠️ [{email}] Attempt {attempt}: Proxy/SMTP error - {msg}")
            time.sleep(1)
            continue

        logging.info(f"🔍 [{email}] [{code}] {msg}")

        if code == 250:
            return email, 'valid', msg
        elif code in RETRY_CODES and attempt < MAX_RETRIES:
            time.sleep(1)
            continue
        else:
            return email, 'invalid', msg

    return email, 'unknown', 'Max retries exceeded'


def load_emails(file_path="permutations.txt"):
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"{file_path} not found.")
        with path.open("r") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"Failed to read email list: {e}")
        return []


def verify_batch(emails):
    results = []
    for email in emails:
        result = verify_email(email)
        results.append(result)
        logging.info(f"✅ [{result[1]}] {result[0]} – {result[2]}")
    return results


if __name__ == "__main__":
    emails = load_emails("permutations.txt")
    if not emails:
        logging.error("No emails found in permutations.txt. Exiting.")
        exit(1)

    logging.info(f"Loaded {len(emails)} emails from permutations.txt")
    results = verify_batch(emails)

    print("\nFinal Results:\n")
    for email, status, reason in results:
        print(f"{email}: {status} - {reason}")
