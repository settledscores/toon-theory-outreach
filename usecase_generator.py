import os
import re
import json
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

INPUT_PATH = "leads/scraped_leads.json"
MAX_SERVICES_LENGTH = 1000

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def postprocess_output(text):
    lines = text.splitlines()
    return " | ".join([
        line.strip() for line in lines
        if line.strip() and not re.match(r"(?i)^here\s+(is|are)\b", line.strip())
    ])

def generate_use_cases(services):
    prompt = f"""
Based on the company's services below, list 4 to 6 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a gerund (e.g., Showing, Explaining, Clarifying, Walking through)
- Be short (under 20 words)
- Be clear, natural, and human — avoid jargon or corporate language
- Directly relate to the company's actual services

Do not mention the company name.
Do not include any labels, intros, or explanations — just return the raw list, separated by the "|" as a delimiter.

Services:
{services}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500,
        )
        return postprocess_output(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"❌ Error generating use cases: {e}")
        return None

def main():
    print("🚀 Generating use cases from scraped_leads.json...")
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return

    updated = 0
    for record in data.get("records", []):
        services = record.get("services", "").strip()
        existing = record.get("use cases", "").strip()

        if not services or existing:
            continue

        print(f"🔍 Processing: {record.get('business name', '[no name]')}")
        use_cases = generate_use_cases(services[:MAX_SERVICES_LENGTH])

        if use_cases:
            record["use cases"] = use_cases
            updated += 1
            print("✅ Use cases added")
        else:
            print("⚠️ Skipped due to generation issue")

        time.sleep(6)  # Throttle to 10 req/min

    try:
        with open(INPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n🎯 Done. {updated} records updated in scraped_leads.json.")
    except Exception as e:
        print(f"❌ Failed to save updates: {e}")

if __name__ == "__main__":
    main()
