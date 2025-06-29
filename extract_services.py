import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INPUT_PATH = "leads/scraped_leads.json"
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
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def main():
    print("🚀 Extracting services from scraped_leads.json...")

    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load scraped_leads.json: {e}")
        return

    updated = 0
    for record in data.get("records", []):
        full_text = record.get("web copy", "")
        services_text = record.get("services", "")
        website = record.get("website url", "[no website]")

        if not full_text.strip() or services_text.strip():
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

    try:
        with open(INPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n🎯 Done. {updated} records updated in scraped_leads.json.")
    except Exception as e:
        print(f"❌ Failed to write updates to scraped_leads.json: {e}")

if __name__ == "__main__":
    main()
