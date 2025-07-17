import os
import re
import json
import signal
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_PATH = "leads/scraped_leads.ndjson"
TEMP_PATH = "leads/scraped_leads.tmp.ndjson"
API_TIMEOUT_SECONDS = 60

bad_response_patterns = [
    r"(?i)\bthis\s+business\s+(offers|provides)",
    r"(?i)\bhere\s+(here are|is)\b",
    r"(?i)\bi\s+(cannot|as an|can’t|can't)\b",
    r"(?i)\bi\s+(apologize|sorry|regret)\b",
    r"(?i)\bthe\s+(services|offerings)\s+are\b",
    r"(?i)\bbased\s+on\s+(the\s+)?(input|description|information)\b"
]

def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")

def is_ambiguous(text):
    if len(text.split()) < 30:
        return True
    if text.lower().count("incubator") > 2 or text.lower().count("member portal") > 2:
        return True
    if re.search(r"(lorem ipsum|under construction|click here|find a business|faq|contact us)", text.lower()):
        return True
    return False

def generate_prompt(web_copy):
    prompt = f"""
Your task is to extract and return exactly three distinct business services mentioned in the messy web copy below.

⚠️ Formatting Rules (MUST follow):
- All service names must be lowercase unless it's a common industry abbreviation like CPA, HR, SaaS, AI, etc.
- Each service must be 1 to 3 words long.
- Output format: service1 | service2 | service3
- No introductions, assistant text, explanations, or extra commentary.
- Do not include phrases like \"this business offers\" or \"here are\".
- The output must be a single line — exactly three services, pipe-separated with spaces.

❌ If the output violates these rules, it will be rejected.

---

Below are examples of raw, messy web copy and their cleaned three-service outputs:

Example 1:
Web copy:
\"Certified Public Accountants - Huebner, Dooley & McGinness, P.S. Learn more. Accounting Services. We guide our clients through tax planning and preparation decisions. Our forensic accounting services can be used in litigation, investigations. Estate and Trust Planning. We help you reach your financial goals and maintain independence. Certified Public Accountants serving the Pacific Northwest.\"

→ tax planning | forensic accounting | financial advisory

Example 2:
Web copy:
\"Business consulting for small businesses, including strategy sessions, marketing audits, and operations optimization. We specialize in helping startups find product-market fit, organize teams, and improve execution.\"

→ business strategy | marketing audits | operations consulting

Example 3:
Web copy:
\"Human Resources services including payroll support, onboarding systems, compliance documentation, and hiring workflows. Our HR experts help you stay ahead of state and federal labor laws.\"

→ HR compliance | payroll support | income tax planning

---

Now extract the services from the web copy below.

Web copy:
{web_copy}
""".strip()
    return prompt

def extract_services(raw_text):
    cleaned = raw_text.strip()

    for pattern in bad_response_patterns:
        if re.search(pattern, cleaned):
            print(f"⚠️ Assistant-style text detected, skipping: {cleaned}", flush=True)
            return None

    parts = [s.strip() for s in cleaned.split("|")]
    if len(parts) != 3:
        print(f"⚠️ Not exactly 3 services: {cleaned}", flush=True)
        return None

    for part in parts:
        if not part or len(part.split()) > 3:
            print(f"⚠️ Invalid service: {part}", flush=True)
            return None
        if not re.fullmatch(r"[a-z0-9\s]+|[A-Z]{2,4}", part):
            print(f"⚠️ Fails lowercase or acronym rule: {part}", flush=True)
            return None

    return " | ".join(parts)

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
        initial_date = record.get("initial date", "")
        website = record.get("website url", "[no website]")

        if not full_text.strip():
            print("⚠️ Empty 'web copy' field, skipping", flush=True)
            results.append(record)
            continue

        if initial_date.strip():
            print("ℹ️ 'initial date' present, skipping", flush=True)
            results.append(record)
            continue

        if is_ambiguous(full_text):
            print("⚠️ Web copy flagged as ambiguous or low quality, skipping", flush=True)
            results.append(record)
            continue

        prompt = generate_prompt(full_text)
        print(f"🔍 Extracting services for: {website}", flush=True)

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(API_TIMEOUT_SECONDS)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100,
            )

            signal.alarm(0)

            raw_output = response.choices[0].message.content.strip()
            print(f"🧬 Raw LLM output → {raw_output}", flush=True)

            parsed = extract_services(raw_output)
            if not parsed:
                print("⚠️ Skipping record due to bad output", flush=True)
                results.append(record)
                continue

            record["services"] = parsed
            updated += 1
            print(f"✅ Services field updated → {parsed}", flush=True)

        except TimeoutError as te:
            print(f"❌ API call timed out: {te}", flush=True)
        except Exception as e:
            print(f"❌ Error generating services: {e}", flush=True)

        results.append(record)

    try:
        write_ndjson(results, TEMP_PATH)
        os.replace(TEMP_PATH, INPUT_PATH)
        print(f"\n🌟 Done. {updated} records updated in scraped_leads.ndjson.", flush=True)
    except Exception as e:
        print(f"❌ Failed to write updates to NDJSON: {e}", flush=True)

if __name__ == "__main__":
    main()
