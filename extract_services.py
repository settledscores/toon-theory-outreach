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

def is_ambiguous(text):
    # Check for gibberish or marketing boilerplate
    if len(text.split()) < 30:
        return True
    if text.lower().count("incubator") > 2 or text.lower().count("member portal") > 2:
        return True
    if re.search(r"(lorem ipsum|under construction|click here|find a business)", text.lower()):
        return True
    return False

def generate_prompt(text):
    examples = """
Example 1:
Web copy: “We help business owners with tax planning, payroll support, and bookkeeping.”
→ This business offers tax planning, payroll support, and bookkeeping.

Example 2:
Web copy: “Our team provides DEI coaching, HR advisory, and employee mediation services to small organizations.”
→ This business offers DEI coaching, HR advisory, and employee mediation.

Example 3:
Web copy: “We guide nonprofits through campaign compliance, grant reporting, and financial management.”
→ This business offers campaign compliance, grant reporting, and financial management.

Example 4:
Web copy: “From startup strategy to long-term CFO partnerships, we help companies grow and scale.”
→ This business offers startup strategy and CFO partnerships.

Now extract a one-sentence summary of services from the following messy business web copy:

{text}
"""
    return examples.strip()

def postprocess_output(text):
    # Grab first sentence and normalize
    sentence = text.strip().split(".")[0].strip()
    if not sentence:
        return ""
    if sentence.lower().startswith("this business offers"):
        return sentence + "."
    if sentence.lower().startswith("offers") or sentence.lower().startswith("provides"):
        return "This business " + sentence + "."
    return "This business offers " + sentence + "."

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

        if is_ambiguous(full_text):
            print("⚠️ Web copy too vague or repetitive, skipping", flush=True)
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

            if len(cleaned_output.split()) <= 5 or "offers" not in cleaned_output:
                print("⚠️ Output too vague, skipping update", flush=True)
                results.append(record)
                continue

            record["services"] = cleaned_output
            updated += 1
            print(f"✅ Services field updated → {cleaned_output}", flush=True)

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
