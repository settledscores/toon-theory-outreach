import os
import re
import json
import time
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
                    print(f"❌ Skipping invalid block: {e}", flush=True)
                buffer = ""
    return records

def write_ndjson(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n")

def generate_prompt(services):
    return f"""Based on the company's services below, list 3 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a gerund (e.g., Showing, Explaining, Clarifying, Demonstrating, Describing, Walking through)
- Be short (under 20 words)
- Be clear, natural, and human — avoid jargon or corporate language
- Directly relate to the company's actual services

Do not mention the company name.
Do not include any labels, intros, or explanations — just return the raw list, separated by "|" as a delimiter.

Services:
{services}
"""

def postprocess_output(text):
    lines = text.splitlines()
    cleaned_lines = []

    bad_patterns = [
        r"(?i)^here\s+(is|are)\b", 
        r"(?i)^i\s+apologize\b", 
        r"(?i)^sorry\b", 
        r"(?i)^unfortunately\b", 
        r"(?i)^i\s+(am|’m)\s+(not\s+sure|unable)\b", 
        r"(?i)^based\s+on\s+(the\s+)?(description|limited\s+information)\b", 
        r"(?i)^as\s+(an\s+)?(ai|llm|language\s+model)\b", 
        r"(?i)^i\s+(cannot|can't)\b",
        r"(?i)^this\s+(ai|llm)\s+(cannot|doesn’t|can't|can’t)\b"
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(re.match(pattern, line) for pattern in bad_patterns):
            print(f"❌ Disqualified line: {line}", flush=True)
            return None  # Reject the entire record
        cleaned_lines.append(line)

    return " | ".join(cleaned_lines)

def main():
    print("🎬 Generating use cases from services...", flush=True)

    try:
        records = read_multiline_ndjson(INPUT_PATH)
    except Exception as e:
        print(f"❌ Failed to load NDJSON: {e}", flush=True)
        return

    updated = 0
    results = []

    for i, record in enumerate(records):
        print(f"➡️ Processing record {i+1}/{len(records)}", flush=True)
        services = record.get("services", "").strip()
        website = record.get("website url", "[no website]")
        name = record.get("business name", "[no name]")

        if not services:
            print(f"⚠️ No services for {name}, skipping", flush=True)
            results.append(record)
            continue

        if record.get("use cases", "").strip():
            print(f"ℹ️ Use cases already filled for {name}, skipping", flush=True)
            results.append(record)
            continue

        print(f"🔍 Generating use cases for: {name}", flush=True)
        prompt = generate_prompt(truncate_text(services))

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

            if cleaned_output:
                record["use cases"] = cleaned_output
                updated += 1
                print(f"✅ Added use cases to {name}", flush=True)
            else:
                print(f"⚠️ Skipped {name} due to disqualified content", flush=True)

        except TimeoutError:
            print(f"❌ Timeout while processing {name}", flush=True)
        except Exception as e:
            print(f"❌ Error generating use cases for {name}: {e}", flush=True)

        results.append(record)
        time.sleep(1.2)

    try:
        write_ndjson(results, TEMP_PATH)
        os.replace(TEMP_PATH, INPUT_PATH)
        print(f"\n🎯 Done. {updated} records updated in scraped_leads.ndjson.", flush=True)
    except Exception as e:
        print(f"❌ Failed to write final file: {e}", flush=True)

if __name__ == "__main__":
    main()
