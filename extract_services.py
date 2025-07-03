import os
import re
import json
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

load_dotenv()
configure(api_key=os.getenv("GEMINI_API_KEY"))

model = GenerativeModel("gemini-pro")
INPUT_PATH = "leads/scraped_leads.ndjson"
MAX_INPUT_LENGTH = 20000

def truncate(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def generate_prompt(text):
    return f"""Extract only the actual services provided by the company from the text below.

- No summaries, assistant language, or explanations.
- No intros like “Here are...” or “This company offers...”
- No bullet headers, section titles, or labels.
- Return a list of services only, each on its own line.

{text}"""

def postprocess_output(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if re.match(r"(?i)^(here\s+(is|are)|the\s+company|this\s+company|core\s+services|services\s+include|they\s+offer)", line):
            continue
        if line:
            clean_lines.append(line)
    return " | ".join(clean_lines)

def main():
    print("🔍 Extracting services from web copy...")

    updated = 0
    records = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except:
                continue

            text = record.get("web copy", "").strip()
            website = record.get("website url", "[no website]")
            if not text or record.get("services", "").strip():
                records.append(record)
                continue

            print(f"➡️ {website}")
            prompt = generate_prompt(truncate(text))

            try:
                response = model.generate_content(prompt)
                raw_output = response.text.strip()
                cleaned = postprocess_output(raw_output)
                record["services"] = cleaned
                updated += 1
                print("✅ Services extracted")
            except Exception as e:
                print(f"❌ Error: {e}")

            records.append(record)

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n🎯 Done. {updated} services updated.")

if __name__ == "__main__":
    main()
