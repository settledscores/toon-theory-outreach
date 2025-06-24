import os
import re
from dotenv import load_dotenv
from airtable import Airtable

# Load env vars
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Common job titles and patterns
TITLE_KEYWORDS = [
    "founder", "co-founder", "partner", "managing partner", "principal", "president",
    "ceo", "cfo", "coo", "director", "head of", "vice president", "vp", "manager",
    "associate", "consultant", "strategist", "advisor", "accountant", "controller",
    "cpa", "analyst", "operations", "intern", "coordinator"
]

def extract_team_members(content):
    lines = content.split("\n")
    team_members = []

    for line in lines:
        if len(line) < 10:
            continue
        for title in TITLE_KEYWORDS:
            if title in line.lower():
                name_match = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z]\.?)?\s[A-Z][a-z]+\b', line)
                if name_match:
                    name = name_match[0]
                    team_members.append(f"{name} — {title.title()} (from: {line.strip()})")
                break
    return team_members

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        content = fields.get("content", "")
        if not content:
            continue

        team = extract_team_members(content)
        if not team:
            continue

        try:
            airtable.update(record["id"], {
                "team": "\n".join(team)
            })
            print(f"✅ Team data updated for {fields.get('website url')}")
            updated += 1
        except Exception as e:
            print(f"❌ Failed update: {e}")

    print(f"\n🏁 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
