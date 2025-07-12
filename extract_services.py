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
    # Flag content that is too short or marketing-heavy
    if len(text.split()) < 30:
        return True
    if text.lower().count("incubator") > 2 or text.lower().count("member portal") > 2:
        return True
    if re.search(r"(lorem ipsum|under construction|click here|find a business|faq|contact us)", text.lower()):
        return True
    return False

def generate_prompt(text):
    examples = """
Below are examples of raw, messy web copy and their cleaned one-sentence summaries of services:

Example 1:
Web copy:
"Certified Public Accountants - Huebner, Dooley & McGinness, P.S. Learn more. Accounting Services. We guide our clients through tax planning and preparation decisions. Our forensic accounting services can be used in litigation, investigations. Estate and Trust Planning. We help you reach your financial goals and maintain independence. Certified Public Accountants serving the Pacific Northwest."

→ This business offers tax planning, forensic accounting, estate and trust planning, and financial advisory services.

Example 2:
Web copy:
"Business consulting for small businesses, including strategy sessions, marketing audits, and operations optimization. We specialize in helping startups find product-market fit, organize teams, and improve execution."

→ This business offers business strategy, marketing audits, and operations consulting for startups and small businesses.

Example 3:
Web copy:
"Human Resources services including payroll support, onboarding systems, compliance documentation, and hiring workflows. Our HR experts help you stay ahead of state and federal labor laws."

→ This business offers HR compliance, payroll support, and employee onboarding services.

---

Now write a one-sentence summary of services for the following messy business web copy:

{text}

→
""".strip()
    return examples

def postprocess_output(text):
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
        print(f"\n➡️ Processing record {i+1}/{len(records)}", flush=True)
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

            print(f"🧠 Raw LLM output → {raw_output}", flush=True)
            print(f"🧾 Final cleaned output → {cleaned_output}", flush=True)

            if len(cleaned_output.split()) <= 5 or "offers" not in cleaned_output.lower():
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
