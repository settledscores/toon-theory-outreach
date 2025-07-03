import os
import re
import json
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
INPUT_PATH = "leads/scraped_leads.ndjson"
MAX_SERVICES_LENGTH = 1000

def postprocess_output(text):
    lines = text.splitlines()
    return " | ".join([
        line.strip() for line in lines
        if line.strip() and not re.match(r"(?i)^here\s+(is|are)\b", line.strip())
    ])

def generate_use_cases(services):
    prompt = f"""
Based on the company's services below, list 3 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a gerund (e.g., Showing, Explaining, Clarifying, Demonstrating, Describing, Walking through)
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
    print("🚀 Generating use cases from scraped_leads.ndjson...")

    updated = 0
    records = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except:
                continue

            services = record.get("services", "").strip()
            existing = record.get("use cases", "").strip()

            if not services or existing:
                records.append(record)
                continue

            print(f"🔍 Processing: {record.get('business name', '[no name]')}")
            use_cases = generate_use_cases(services[:MAX_SERVICES_LENGTH])

            if use_cases:
                record["use cases"] = use_cases
                updated += 1
                print("✅ Use cases added")
            else:
                print("⚠️ Skipped due to generation issue")

            records.append(record)
            time.sleep(6)

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
