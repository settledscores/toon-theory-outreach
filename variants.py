import os
import random
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

subject_variants = [
    "Let’s make your message stick",
    "A quick thought for your next project",
    "Helping your ideas stick visually",
    "Turn complex into simple (in 90 seconds)",
    "Your story deserves to be told differently",
    "How about a different approach to your messaging?",
    "Making your ideas unforgettable",
    "Need a visual upgrade for your next launch?"
]

salutation_variants = [
    "Hi {name},",
    "Hey {name},",
    "Hello {name},",
    "Hi there {name},",
    "Hey there {name},",
    "Hey {name}, just a quick note."
]

paragraph1_variants = [
    "I’ve been diving into your work lately, and I think there’s a huge opportunity here.",
    "Your work speaks for itself, but I’ve got an idea that could amplify it even more.",
    "I’ve been checking out your recent projects, and I have a quick thought for you.",
    "Your work stands out on its own; but I've got something that could boost it even more.",
    "Been thinking about how your message could hit harder. Got a minute?",
    "Your work grabbed my attention; now I’ve got an idea to make it even more engaging.",
    "I saw your work and thought: this could use a bit of a visual spark.",
    "You’ve got a great thing going, but here’s something I think could elevate it even more."
]

paragraph2_variants = [
    "Our animations are fully done-for-you: script, voiceover, storyboard, the whole thing; so you don’t have to lift a finger.",
    "We handle everything: scripting, storyboarding, illustrations and narration; so your team can focus on doing what they do best.",
    "You get a strategic video that feels custom-built for your message; no templates or fluff; professionally scripted, voiced, and illustrated; ready to go.",
    "We make the whole process easy, from concept to delivery, with zero effort on your side.",
    "Everything’s included: concept, writing, narration, illustrations; no extra work required from your team.",
    "Each explainer is crafted from scratch to match your voice, story, and audience. You get an end-to-end solution that feels like part of your brand, not just an add-on."
]

paragraph3_variants = [
    "If you already prioritize clear communication and meaningful results, then I think there’s real potential to add a layer of visual storytelling that helps even more people 'get it' faster.",
    "If you already prioritize streamlining complex ideas, we could help bring that to life visually for even greater impact.",
    "If you already prioritize client satisfaction; adding a visual layer might help drive home your value faster and clearer.",
    "If you're already simplifying things for your audience, why not let visuals do some of the heavy lifting too?",
    "If you already prioritize clarity and quality, video could be the next smart move in boosting engagement and trust."
]

paragraph5_variants = [
    "If this sounds interesting, I’d love to chat more about it.",
    "Let me know if you’d like to see a few custom ideas I think could really work for you.",
    "If you’re curious, I’d be happy to share a few relevant samples and see if it aligns with your vision.",
    "No pressure, but if you think this could help, I’d be happy to brainstorm some ideas together.",
    "I can put together a few ideas if you're open to seeing how this could fit your needs.",
    "It’d be fun to explore this idea with you if you’re up for it.",
    "Let me know if you’re open to a quick chat about how this could work for you.",
    "I’m happy to sketch out some ideas and see what resonates. Just let me know.",
    "If you think this is worth a shot, I’d love to share more tailored ideas with you.",
    "I’d love to put together a short demo if this piques your interest."
]

paragraph6_variants = [
    "Appreciate how you keep things thoughtful and real.",
    "Thanks for putting something refreshing out there.",
    "Thanks for leading with both heart and strategy."
]

signature_variants = [
    "Warm regards,\nTrent\nFounder, Toon Theory\nwww.toontheory.com\nWhiteboard Animation For The Brands People Trust",
    "All the best,\nTrent\nToon Theory\nwww.toontheory.com",
    "Cheers,\nTrent\nwww.toontheory.com",
    "Thanks for your time,\nTrent\nFounder at Toon Theory",
    "Take care,\nTrent\nToon Theory\nwww.toontheory.com",
    "Catch you soon,\nTrent\nToon Theory",
    "Sincerely,\nTrent\nToon Theory",
    "Kind regards,\nTrent\nToon Theory",
    "Hope to chat soon,\nTrent\nToon Theory",
    "Looking forward,\nTrent\nwww.toontheory.com"
]

def update_record_fields(record_id, updates):
    airtable.update(record_id, updates)

def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        record_id = record["id"]
        fields = record.get("fields", {})
        name = fields.get("company name", "there")
        
        updates = {}
        if not fields.get("subject"):
            updates["subject"] = random.choice(subject_variants)
        if not fields.get("salutation"):
            updates["salutation"] = random.choice(salutation_variants).replace("{name}", name)
        if not fields.get("paragraph 1 niche opener"):
            updates["paragraph 1 niche opener"] = random.choice(paragraph1_variants)
        if not fields.get("paragraph 2 pitch"):
            updates["paragraph 2 pitch"] = random.choice(paragraph2_variants)
        if not fields.get("paragraph 3 service tiein"):
            updates["paragraph 3 service tiein"] = random.choice(paragraph3_variants)
        if not fields.get("paragraph 5 invitation"):
            updates["paragraph 5 invitation"] = random.choice(paragraph5_variants)
        if not fields.get("paragraph 6 closer"):
            updates["paragraph 6 closer"] = random.choice(paragraph6_variants)
        if not fields.get("signature"):
            updates["signature"] = random.choice(signature_variants)
        
        if updates:
            update_record_fields(record_id, updates)
            updated_count += 1
            print(f"✅ Updated record: {record_id}")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
