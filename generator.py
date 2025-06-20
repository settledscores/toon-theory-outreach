import os
from airtable import Airtable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Airtable config
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

def build_email(fields):
    name = fields.get("name", "there")
    company = fields.get("company name", "your team")
    salutation = fields.get("salutation", f"Hi {name},")
    subject = fields.get("subject", f"A quick note for {company}")

    p1 = fields.get("paragraph 1 niche opener", "")
    p2 = fields.get("paragraph 2 pitch", "")
    p3 = fields.get("paragraph 3 service tiein", "")
    uc1 = fields.get("paragraph 4 use case 1", "")
    uc2 = fields.get("paragraph 4 use case 2", "")
    uc3 = fields.get("paragraph 4 use case 3", "")
    p5 = fields.get("paragraph 5 invitation", "")
    p6 = fields.get("paragraph 6 closer", "")
    sig = fields.get("signature", "Cheers,\nTrent\nwww.toontheory.com")

    email = f"""
{salutation}

{p1}

{p2}

{p3}

Our videos are often used by folks like you to:

1. {uc1}
2. {uc2}
3. {uc3}

{p5}

{p6}

{sig}
"""

    return subject.strip(), email.strip()

def main():
    print("🚀 Generating Email 1 from table fields...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        if "email 1" in fields:
            continue

        subject, body = build_email(fields)
        airtable.update(record["id"], {
            "email 1": body,
            "subject": subject,
            "initial date": datetime.utcnow().isoformat()
        })

        print(f"✅ Composed email for: {fields.get('name', '[No Name]')} | {subject}")
        generated_count += 1

    print(f"\n🎯 Finished. Total emails generated: {generated_count}")

if __name__ == "__main__":
    main()
