import os
import random
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

subject_variants = [
    "Let’s make your message stick",
    "A quick thought for your next project",
    "Helping your message stick visually",
    "Turn complex into simple (in 90 seconds or less)",
    "Your story deserves to be told differently",
    "How about a different approach to your messaging?",
    "Making your message unforgettable",
]

def main():
    print("🚀 Generating Email 1 from table fields...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        if "email 1" in fields:
            continue

        name = fields.get("name", "there")
        company = fields.get("company name", "your team")
        summary_2 = fields.get("niche summary paragraph 2", "").strip()

        salutation = fields.get("salutation", f"Hi {name},")
        subject = fields.get("subject") or random.choice(subject_variants)
        p1 = fields.get("paragraph 1 niche opener", "")
        p2 = fields.get("paragraph 2 pitch", "")
        p3 = fields.get("paragraph 3 service tiein", "").replace("[niche summary paragraph 2]", summary_2)
        uc1 = fields.get("paragraph 4 use case 1", "")
        uc2 = fields.get("paragraph 4 use case 2", "")
        uc3 = fields.get("paragraph 4 use case 3", "")
        p4b = fields.get("paragraph 4b benefits", "")
        p5 = fields.get("paragraph 5 invitation", "").replace("[company name]", company)
        p6 = fields.get("paragraph 6 closer", "")
        p7 = fields.get("paragraph 7 cta", "")
        sig = fields.get("signature", "Cheers,\nTrent\nwww.toontheory.com")

        email_body = f"""
{salutation}

{p1}

{p2}

{p3}

1. {uc1}
2. {uc2}
3. {uc3}

{p4b}

{p5}

{p7}

{p6}

{sig}
""".strip()

        airtable.update(record["id"], {
            "email 1": email_body,
            "subject": subject.strip()
        })

        print(f"✅ Composed email for: {fields.get('name', '[No Name]')} | {subject}")
        generated_count += 1

    print(f"\n🎯 Finished. Total emails generated: {generated_count}")

if __name__ == "__main__":
    main()
