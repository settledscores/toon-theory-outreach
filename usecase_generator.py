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
TEMP_PATH = "leads/scraped_leads.tmp.ndjson"

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

def read_multiline_ndjson(path):
    buffer, records = "", []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip() == "}":
                try:
                    records.append(json.loads(buffer))
                except Exception as e:
                    print(f"❌ Skipping invalid block: {e}")
                buffer = ""
    return records

def main():
    print("🎬 Generating use cases...")

    updated = 0
    records = read_multiline_ndjson(INPUT_PATH)

    with open(TEMP_PATH, "w", encoding="utf-8") as out_f:
        for record in records:
            services = record.get("services", "").strip()
            name = record.get("business name", "[no name]")

            if not services or record.get("use cases", "").strip():
                json.dump(record, out_f, indent=2, ensure_ascii=False)
                out_f.write("\n")
                continue

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

            json.dump(record, out_f, indent=2, ensure_ascii=False)
            out_f.write("\n")
            time.sleep(1.2)

    os.replace(TEMP_PATH, INPUT_PATH)
    print(f"\n🎯 Done. {updated} use cases updated.")

if __name__ == "__main__":
    main()
