import os
import re
import json
import signal
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INPUT_PATH = "leads/scraped_leads.ndjson"
TEMP_PATH = "leads/scraped_leads.tmp.ndjson"
MAX_INPUT_LENGTH = 14000
API_TIMEOUT_SECONDS = 60

def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")

def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def generate_prompt(text):
    return f"""Extract only the actual services provided by the company from the text below.

- No explanations, summaries, or assistant language.
- No intros like “Here are...”, “This company offers...”, or “The core services include...”.
- No bullet headers or section titles.
- Just return the raw list of service lines, one per line, with no extra wording or formatting.
- Ensure that all the content generated is in lowercase form, any output that is not in lowercase will be voided. this rule applies across the board except in specialized cases such as industry abbreviations, for example HR, B2B, SaaS, DEI, API, SEO, UX, UI, AI, IRS, etc. this abbreviations can capitalize as necessary.
- All output should be 1 to 3 words max, avoid verbose and irrelevant context. For example, instead of saying 'Implementation of HR, Payroll, Performance and Human Capital Management systems' you can say 'payroll processing', 'HCM implementation' or 'HR consultation'
- Each service line should be short: no more than 3 words per line.
- Return a maximum of 3 lines.

here is an example of good input and output

input:
"HR & Payroll Implementation and Optimization for Small and Mid-size Organizations info@hr1systems.com Better Implement, Better Tech! We care about your business and description: Which is why our philosophy is Our Features Powerful, Tailored Solutions for Your HR and Payroll Needs Our features are designed to streamline your operations, ensure..."

good output:
payroll processing
HR consultation
HCM implementation

{text}
"""

def postprocess_output(text):
    lines = text.splitlines()
    clean_phrases = []
    for line in lines:
        line = line.strip()
        if re.match(r"(?i)^(here\s+(is|are)|the\s+company|this\s+company|core\s+services|services\s+include|they\s+offer)", line):
            continue
        if line:
            clean_phrases.append(line.lower())
    clean_phrases = [p for p in clean_phrases if 1 <= len(p.split()) <= 5]
    return " | ".join(clean_phrases[:3])

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
                    print(f"❌ Skipping invalid record: {e}", flush=True)
                buffer = ""
    return records

def write_ndjson(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n")

def main():
    print("🚀 Extracting services from scraped_leads.ndjson...", flush=True)

    try:
        records = read_multiline_ndjson(INPUT_PATH)
    except Exception as e:
        print(f"❌ Failed to load NDJSON: {e}", flush=True)
        return

    updated = 0
    results = []

    for i, record in enumerate(records):
        print(f"➡️ Processing record {i+1}/{len(records)}", flush=True)
        full_text = record.get("web copy", "")
        services_text = record.get("services", "")
        website = record.get("website url", "[no website]")

        if not full_text.strip():
            print("⚠️ Empty 'web copy' field, skipping", flush=True)
            results.append(record)
            continue

        if services_text.strip():
            print("ℹ️ 'services' already filled, skipping", flush=True)
            results.append(record)
            continue

        print(f"🔍 Extracting services for: {website}", flush=True)
        prompt = generate_prompt(truncate_text(full_text))

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(API_TIMEOUT_SECONDS)

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            signal.alarm(0)

            raw_output = response.choices[0].message.content.strip()
            cleaned_output = postprocess_output(raw_output)
            service_count = cleaned_output.count("|") + 1 if cleaned_output else 0

            if 1 <= service_count <= 3:
                record["services"] = cleaned_output
                updated += 1
                print(f"✅ Services field updated → {cleaned_output}", flush=True)
            else:
                print(f"⚠️ Invalid service count ({service_count}), skipping update. Output: {cleaned_output}", flush=True)

        except TimeoutError as te:
            print(f"❌ API call timed out: {te}", flush=True)
        except Exception as e:
            print(f"❌ Error generating services: {e}", flush=True)

        results.append(record)

    try:
        write_ndjson(results, TEMP_PATH)
        os.replace(TEMP_PATH, INPUT_PATH)
        print(f"\n🎯 Done. {updated} records updated in scraped_leads.ndjson.", flush=True)
    except Exception as e:
        print(f"❌ Failed to write updates to NDJSON: {e}", flush=True)

if __name__ == "__main__":
    main()
