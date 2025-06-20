import os
from airtable import Airtable
from dotenv import load_dotenv

# Load .env credentials
load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Variant content
subject_variants = """Let’s make your message stick
A quick thought for your next project
Helping your ideas pop visually
Turn complex into simple (in 90 seconds)
Your story deserves to be told differently
One quick thing that might help
Let’s give your brand a fresh twist
How about a different approach to your messaging?
Making your ideas unforgettable
Need a visual upgrade for your next launch?"""

opener_variants = """I’ve been diving into your work lately, and I think there’s a huge opportunity here.
Your work speaks for itself, but I’ve got an idea that could amplify it even more.
I’ve been checking out your recent projects, and I have a quick thought for you.
I couldn’t help but notice how your work stands out — I’d love to throw an idea your way.
Been thinking about how your message could hit harder. Got a minute?
I love the energy behind what you’re doing — got something that could boost it even more.
Your projects grabbed my attention — now I’ve got a quick idea to make them even more engaging.
I saw your brand and thought: this could use a bit of a visual spark.
You’ve got a great thing going, but here’s something I think could elevate it even more.
I’ve been following your work, and there’s an angle I think could really connect."""

closer_variants = """If this sounds interesting, I’d love to chat more about it.
Let me know if you’d like to see a few custom ideas I think could really work for you.
If you’re curious, I’d be happy to share a few samples and see if it aligns with your vision.
No rush, but if you think this could help, I’d be happy to brainstorm some ideas together.
I can put together a few ideas if you're open to seeing how this could fit your needs.
It’d be fun to explore this idea with you if you’re up for it.
Let me know if you’re open to a quick chat about how this could work for you.
I’m happy to sketch out some ideas and see what resonates. Just let me know.
If you think this is worth a shot, I’d love to share more tailored ideas with you.
I’d love to put together a few visuals if this piques your interest."""

# Main update loop
def update_records():
    records = airtable.get_all()
    count = 0
    for record in records:
        record_id = record["id"]
        fields = record.get("fields", {})

        if not all(k in fields for k in ["subject variants", "opener variants", "closer variants"]):
            airtable.update(record_id, {
                "subject variants": subject_variants,
                "opener variants": opener_variants,
                "closer variants": closer_variants,
            })
            count += 1
            print(f"✅ Updated record {record_id}")

    print(f"\n🎯 Done. {count} records updated.")

if __name__ == "__main__":
    update_records()
