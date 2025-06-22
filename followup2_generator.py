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

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could simplify something {company} is working on — a product, a process, or a pitch.

Happy to mock up a short demo or even draft a script. Totally no-strings — just a creative way to explore the idea.

{signature}""",

    """Hi {name},

Still happy to offer a quick sketch or sample if it’s helpful. A lot of our clients use whiteboard animation to break down services for new hires, investors, or even clients.

If {company} has anything you’re trying to simplify or visualize, I’d love to help.

{signature}""",

    """Hi {name},

Wanted to follow up again before I close the loop here.

If animation could help {company} clarify a message or show off a service, I’d be glad to create a short teaser. It’s a quick, visual way to get the conversation going — no cost at all.

{signature}""",

    """Hi {name},

Not trying to spam you — just wanted to keep the door open.

If {company} ever needs a clear, visual way to communicate something complex, I’d love to create a custom sketch or sample explainer.

Thanks for considering,
{signature}""",

    """Hi {name},

I know inboxes get busy. Just offering one last check-in.

Animation’s a helpful tool when you need to simplify a process, explain a strategy, or just keep people’s attention. If {company} ever wants to give it a try, I’d be happy to share a short teaser.

Hope things are going well on your end,
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
