import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INPUT_PATH = "leads/scraped_leads.ndjson"
MAX_INPUT_LENGTH = 14000

def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def generate_prompt(text):
    return f"""Extract only the actual services provided by the company from the text below.

- No explanations, summaries, or assistant language.
- No intros like “Here are...”, “This company offers...”, or “The core services include...”.
- No bullet headers or section titles.
- Just return the raw list of service lines, one per line, with no extra wording or formatting.

{text}
"""

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
    print("🚀 Extracting services from scraped_leads.ndjson...")
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        return

    updated = 0
    records = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except Exception:
                continue

            full_text = record.get("web copy", "").strip()
            services_text = record.get("services", "").strip()
            website = record.get("website url", "[no website]")

            if not full_text or services_text:
                records.append(record)
                continue

            print(f"🔍 Extracting services for: {website}")
            prompt = generate_prompt(truncate_text(full_text))

            try:
                response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000,
                )

                raw_output = response.choices[0].message.content.strip()
                cleaned_output = postprocess_output(raw_output)

                record["services"] = cleaned_output
                updated += 1
                print("✅ Services field updated")

            except Exception as e:
                print(f"❌ Error generating services: {e}")

            records.append(record)

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
