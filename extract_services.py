import os
import re
import json
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

load_dotenv()
configure(api_key=os.getenv("GEMINI_API_KEY"))

model = GenerativeModel("gemini-1.5-flash")
INPUT_PATH = "leads/scraped_leads.ndjson"
TEMP_PATH = "leads/scraped_leads.tmp.ndjson"
MAX_INPUT_LENGTH = 20000

def truncate(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def generate_prompt(text):
    return f"""Extract only the actual services provided by the company from the text below.

- No explanations, summaries, or assistant language.
- No intros like “Here are...”, “This company offers...”, or “The core services include...”.
- No bullet headers or section titles.
- Just return the raw list of service lines, one per line, with no extra wording or formatting.

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
    print("🔍 Extracting services from web copy...")

    updated = 0
    records = read_multiline_ndjson(INPUT_PATH)

    with open(TEMP_PATH, "w", encoding="utf-8") as out_f:
        for record in records:
            text = record.get("web copy", "").strip()
            website = record.get("website url", "[no website]")
            if not text or record.get("services", "").strip():
                json.dump(record, out_f, indent=2, ensure_ascii=False)
                out_f.write("\n")
                continue

            print(f"➡️ {website}")
            try:
                prompt = generate_prompt(truncate(text))
                response = model.generate_content([prompt])
                raw_output = response.text.strip()
                cleaned = postprocess_output(raw_output)
                record["services"] = cleaned
                updated += 1
                print("✅ Services extracted")
            except Exception as e:
                print(f"❌ Error: {e}")

            json.dump(record, out_f, indent=2, ensure_ascii=False)
            out_f.write("\n")

    os.replace(TEMP_PATH, INPUT_PATH)
    print(f"\n🎯 Done. {updated} services updated.")

if __name__ == "__main__":
    main()
