import os
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
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_gerunds(use_cases):
    prompt = f"""Convert each of the following lines into lowercase continuous gerund phrases, suitable for inline use. Only modify the *first word* into the -ing form. Do not reword, remove, or reorder anything. Return only the rewritten lines, one per line. No preamble, no assistant voice, no markdown, no explanations.

{use_cases}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256
        )
        return response.choices[0].message.content.strip().splitlines()
    except Exception as e:
        print(f"❌ Error from Groq: {e}")
        return []

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        record_id = record["id"]

        uc1 = fields.get("paragraph 4 use case 1", "")
        uc2 = fields.get("paragraph 4 use case 2", "")
        uc3 = fields.get("paragraph 4 use case 3", "")

        inline1 = fields.get("paragraph 4 use case 1 inline", "")
        inline2 = fields.get("paragraph 4 use case 2 inline", "")
        inline3 = fields.get("paragraph 4 use case 3 inline", "")

        if not any([uc1, uc2, uc3]):
            continue  # no use cases to process

        if all([inline1, inline2, inline3]):
            continue  # all inline versions already exist

        use_case_block = "\n".join(filter(None, [uc1, uc2, uc3]))
        gerunds = generate_gerunds(use_case_block)

        updates = {}
        if uc1 and not inline1 and len(gerunds) > 0:
            updates["paragraph 4 use case 1 inline"] = gerunds[0]
        if uc2 and not inline2 and len(gerunds) > 1:
            updates["paragraph 4 use case 2 inline"] = gerunds[1]
        if uc3 and not inline3 and len(gerunds) > 2:
            updates["paragraph 4 use case 3 inline"] = gerunds[2]

        if updates:
            airtable.update(record_id, updates)
            updated += 1
            print(f"✅ Updated: {record_id}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
