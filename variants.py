import os
import random
import re
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Groq setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# --- Variants ---
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
    "Hi {name},", "Hey {name},", "Hello {name},",
    "Hi there {name},", "Hey there {name},",
    "Hey {name}, just a quick note."
]

default_paragraph1_variants = [
    "I’ve been diving into your work lately, and I think there’s a huge opportunity here.",
    "Your work speaks for itself, but I’ve got an idea that could amplify it even more.",
    "I’ve been checking out your recent projects, and I have a quick thought for you.",
    "Your work stands out on its own; but I've got something that could boost it even more.",
    "Been thinking about how your message could hit harder. Got a minute?",
    "Your work grabbed my attention; now I’ve got an idea to make it even more engaging.",
    "I saw your work and thought: this could use a bit of a visual spark.",
    "You’ve got a great thing going, but here’s something I think could elevate it even more."
]

paragraph1_templates = [
    "I’ve been following {company} lately, and your focus on {summary} really got my attention.",
    "I came across {company} recently, your approach to {summary} really got my attention.",
    "I’ve been exploring what {company} does, and your focus on {summary} caught my eye.",
]

paragraph2_variants = [
    "I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education."
]

paragraph3_intro_phrases = [
    "With your mission centered on", 
    "Since you're focused on"
]

paragraph3_variants = [
    "{phrase} {summary_2}, animated storytelling could supercharge your message for even greater impact. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you to:"
]

paragraph3_additional_variants = [
    "With your focus on {summary_2}, I think there’s real potential to add a layer of visual storytelling that helps even more people 'get it' faster. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you to:",
    "With your focus on {summary_2}, animated storytelling could help supercharge your message for even greater impact. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you to:",
    "With your focus on {summary_2}, animated storytelling might help drive home your message faster and clearer. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you to:",
    "With your focus on {summary_2}, animated storytelling could be the next smart move in boosting engagement and trust. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you to:"
]

paragraph4b_variants = [
    "These videos often help businesses increase engagement by up to 60%, double conversion rates, and boost message retention by up to 80%.",
    "Our clients often see up to 2x engagement and 80% stronger retention when they present ideas visually.",
    "These animations don’t just explain, they convert; often doubling engagement, boosting sales and improving trust.",
]

paragraph5_variants = [
    "If you'd be open to it, I’d love to share a brief demo tailored to one of your core offerings. This could be a sample script or a ten second sketch. All at zero cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "If you’re open to it, I’d love to share a quick sketch or sample script tailored to one of your key offerings at zero cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "I'd be happy to draft a no-cost, ten-second demo around something core to your brand. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "Would you be open to seeing a quick script or ten-second sketch built with {company} in mind? Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it."
]

paragraph6_variants = [
    "Thanks for putting something refreshing out there.",
    "Thanks for leading with both heart and strategy.",
    "Keep doing what you do, it's making an impact.",
]

paragraph7_cta_variants = [
    "Feel free to reply if you’d like to explore what this could look like.",
    "If it sounds interesting, a quick reply is all it takes to get started."
]

signature_variants = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Catch you soon,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Kind regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Hope to chat soon,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Looking forward,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

# --- Groq-powered gerund conversion ---
def generate_smart_gerund(phrase):
    try:
        prompt = f"Convert this sentence into a lowercase gerund phrase. No intro, no summary, no explanations, no summary, enforce strict all-lowercase policy. Just the raw phrase:\n\n{phrase}"
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Error with Groq: {e}")
        return ""

# --- Main Logic ---
def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        record_id = record["id"]
        fields = record.get("fields", {})
        name = fields.get("name") or fields.get("contact name") or "there"
        company = fields.get("company name", "your company")
        summary_1 = fields.get("niche summary paragraph", "").strip()
        summary_2 = fields.get("niche summary paragraph 2", "").strip()

        updates = {}

        if not fields.get("subject"):
            updates["subject"] = random.choice(subject_variants)

        if not fields.get("salutation"):
            updates["salutation"] = random.choice(salutation_variants).format(name=name)

        if not fields.get("paragraph 1 niche opener"):
            if summary_1:
                updates["paragraph 1 niche opener"] = random.choice(paragraph1_templates).format(company=company, summary=summary_1)
            else:
                updates["paragraph 1 niche opener"] = random.choice(default_paragraph1_variants)

        if not fields.get("paragraph 2 pitch"):
            updates["paragraph 2 pitch"] = random.choice(paragraph2_variants)

        if not fields.get("paragraph 3 service tiein") and summary_2:
            phrase = random.choice(paragraph3_intro_phrases)
            main_variant = random.choice(paragraph3_variants).format(phrase=phrase, summary_2=summary_2)
            alternate = random.choice(paragraph3_additional_variants).format(summary_2=summary_2)
            updates["paragraph 3 service tiein"] = random.choice([main_variant, alternate])

        # Grab use cases
        uc1 = fields.get("paragraph 4 use case 1", "").strip()
        uc2 = fields.get("paragraph 4 use case 2", "").strip()
        uc3 = fields.get("paragraph 4 use case 3", "").strip()

        # Use Groq to generate inline versions
        if uc1 and not fields.get("paragraph 4 use case 1 inline"):
            updates["paragraph 4 use case 1 inline"] = generate_smart_gerund(uc1)
        if uc2 and not fields.get("paragraph 4 use case 2 inline"):
            updates["paragraph 4 use case 2 inline"] = generate_smart_gerund(uc2)
        if uc3 and not fields.get("paragraph 4 use case 3 inline"):
            updates["paragraph 4 use case 3 inline"] = generate_smart_gerund(uc3)

        if not fields.get("paragraph 4b benefits"):
            updates["paragraph 4b benefits"] = random.choice(paragraph4b_variants)

        if not fields.get("paragraph 5 invitation"):
            updates["paragraph 5 invitation"] = random.choice(paragraph5_variants).format(company=company)

        if not fields.get("paragraph 6 closer"):
            updates["paragraph 6 closer"] = random.choice(paragraph6_variants)

        if not fields.get("paragraph 7 cta"):
            updates["paragraph 7 cta"] = random.choice(paragraph7_cta_variants)

        if not fields.get("signature"):
            updates["signature"] = random.choice(signature_variants)

        if updates:
            airtable.update(record_id, updates)
            updated_count += 1
            print(f"✅ Updated record: {record_id}")
            print(f"   → Fields updated: {list(updates.keys())}")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
