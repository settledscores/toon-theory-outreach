import os
import re
import json
import time
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

load_dotenv()
configure(api_key=os.getenv("GEMINI_API_KEY"))

model = GenerativeModel("gemini-pro")
INPUT_PATH = "leads/scraped_leads.ndjson"

def postprocess_output(text):
    lines = text.splitlines()
    return " | ".join([
        line.strip() for line in lines
        if line.strip() and not re.match(r"(?i)^here\s+(is|are)\b", line.strip())
    ])

def generate_prompt(services):
    return f"""Based on the company's services below, list 3 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a gerund (e.g., Showing, Explaining, Clarifying, Demonstrating, Describing, Walking through)
- Be short (under 20 words)
- Be clear, natural, and human — avoid jargon or corporate language
- Directly relate to the company's actual services

Do not mention the company name.
Do not include any labels, intros, or explanations — just return the raw list, separated by the "|" as a delimiter..

Services:
{services}
"""

def main():
    print("🎬 Generating use cases...")

    updated = 0
    records = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except:
                continue

            services = record.get("services", "").strip()
            if not services or record.get("use cases", "").strip():
                records.append(record)
                continue

            name = record.get("business name", "[no name]")
            print(f"➡️ {name}")
            prompt = generate_prompt(services)

            try:
                response = model.generate_content(prompt)
                raw_output = response.text.strip()
                cleaned = postprocess_output(raw_output)
                record["use cases"] = cleaned
                updated += 1
                print("✅ Use cases added")
            except Exception as e:
                print(f"❌ Error: {e}")

            records.append(record)
            time.sleep(1.2)

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n🎯 Done. {updated} use cases updated.")

if __name__ == "__main__":
    main()
