import os
import smtplib

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

print(f"🧪 Testing SMTP connection to {SMTP_SERVER}:{SMTP_PORT}…")

try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    print("✅ SMTP connection successful and authenticated!")
except Exception as e:
    print("❗ SMTP test failed:", type(e).__name__, "-", e)
    exit(1)
