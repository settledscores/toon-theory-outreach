import os
import random
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

TEMPLATES = [
    """Hi {name},

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could simplify something {company} is working on: a product, a new launch, or a pitch.

Happy to mock up a short demo or even draft a script. Totally no-strings; just a creative way to explore the idea.

If it sounds worth exploring, feel free to reply. You’ll find a link to our website in my signature if you’d like to take a peek at some of our recent projects.

{signature}""",

    """Hey {name},

Still happy to offer a quick sketch or sample if it’s helpful. A lot of our clients use whiteboard animation to break down services for new hires, investors, or even clients.

If {company} has anything you’re trying to simplify or visualize, I’d love to help.

Reply anytime if this feels like a fit. There’s a link to our website in the signature if you’d like to see some examples of some of our previous work.

{signature}""",

    """Hello {name},

Wanted to follow up again before I close the loop here.

If animation could help {company} break down the dense copy or show off an awesome new feature, I’d be glad to draft a script or create a short teaser. It’s a quick, visual way to get the conversation going; no cost at all.

Reply anytime if this feels like a fit. There’s a link to our website in the signature if you’d like to see some examples of some of our previous work.

{signature}""",

    """Hi there {name},

I know inboxes get busy. Just offering one last check-in.

Animation’s a helpful tool when you need to simplify a process, explain a strategy, or just keep people’s attention.

If {company} ever wants to give it a try, I’d be happy to share a short teaser.

If it sounds worth exploring, feel free to reply. You’ll find a link to our website in my signature if you’d like to take a peek at some of our recent projects.

{signature}"""
]

def build_email(template, name, company, signature):
    return template.format(name=name, company=company, signature=signature)

def main():
    print("🚀 Generating randomized follow-up 2 emails...")
    records = airtable.get_all()
    eligible_records = []

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        signature = fields.get("signature", "").strip()
        email3 = fields.get("email 3", "").strip()

        if name and company and signature and not email3:
            eligible_records.append((record["id"], name, company, signature))

    if not eligible_records:
        print("⚠️ No eligible records found.")
        return

    random.shuffle(eligible_records)
    random.shuffle(TEMPLATES)

    updated = 0
    for i, (record_id, name, company, signature) in enumerate(eligible_records):
        template = TEMPLATES[i % len(TEMPLATES)]
        message = build_email(template, name, company, signature)
        airtable.update(record_id, {"email 3": message})
        updated += 1
        print(f"✅ Email 3 populated for: {record_id}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
