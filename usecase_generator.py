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
    return f"""
Based on the company's services below, list 3 *explainer video use cases* that clearly show the value of what they offer.

Each bullet must:
- Be short (under 20 words)
- Sound natural and human — no corporate speak or vague jargon
- Be specific to the service or customer benefit
- Be something you’d *want to see* in a short, animated explainer video
- Avoid generic fluff like "improving productivity", "streamlining operations", "simplifying processes", etc.
- Sound like the examples below — benefit-led, visual, concrete

Format the result as a **single line** with 3 bullets separated by "|" (pipe character).

---

### Examples of Good Use Cases:

**Accounting / Finance**
- Showing how outsourced CFOs double cash visibility in 90 seconds
- Framing your bookkeeping as clean, easy monthly reports without the extra spreadsheets
- Explaining how tax prep saves businesses thousands in missed deductions

**Payroll / HR**
- Showing how your payroll service auto-handles IRS compliance for small teams of 5–50
- Mapping how outsourced HR avoids 3 months of hiring risk
- Visualizing HR onboarding with zero paperwork and same-day access

**Legal / Compliance**
- Turning complex contract terms into 90-second client explainers
- Showing how mediation saves 4+ months of legal delays

**Consulting / Strategy**
- Mapping your client onboarding journey in 90 seconds
- Showing how strategic planning cuts churn by 25%
- Turning your offer into a story — not a sales pitch

**Coaching / Training**
- Visualizing how your coaching turns “busy” into “profitable”
- Framing leadership development as team transformation, not just soft skills
- Showing how habit coaching boosts client retention by 2x

**Health / Wellness**
- Mapping the therapy intake process to reduce drop-offs
- Showing how telehealth makes care feel in-person
- Visualizing how your sleep program helps reduce burnout in 2 weeks

**Tech / SaaS**
- Bringing your dashboard features to life with 2-minute visuals
- Showing how automated alerts save reps from cold deals
- Walking users through the setup process — no docs required
- Explaining how a Fractional Analyst actually works without a single spreadsheet

**Logistics / Operations**
- Visualizing supply chain visibility from factory to front door
- Mapping the return process for customers in 30 seconds
- Showing how route optimization saves 10+ hours per week

---

### Keyword-Driven Inference Tips:

Treat the section above as examples — do not reuse them directly.

Services:
{services}
"""

def has_disqualifying_line(text):
    bad_line_patterns = [
        r"(?i)^here\s+(is|are)\b",
        r"(?i)^i\s+apologize\b",
        r"(?i)^sorry\b",
        r"(?i)^unfortunately\b",
        r"(?i)^i\s+(am|’m|‘m)\s+(not\s+sure|unable|an\s+ai|a\s+language\s+model)\b",
        r"(?i)^based\s+on\s+(the\s+)?(description|limited\s+information|input)\b",
        r"(?i)^(as|i am)\s+(an\s+)?(ai|llm|language\s+model)\b",
        r"(?i)^i\s+(cannot|can't|can’t)\b",
        r"(?i)^this\s+(ai|llm|language\s+model)\s+(cannot|can't|can’t|doesn’t)\b"
    ]
    for line in text.splitlines():
        for pattern in bad_line_patterns:
            if re.match(pattern, line.strip()):
                return True
    return False

def postprocess_output(text):
    lines = text.splitlines()
    return " | ".join([line.strip() for line in lines if line.strip()])

def generate_use_cases_with_retries(prompt, retries=1):
    for attempt in range(retries + 1):
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

            output = response.choices[0].message.content.strip()
            if has_disqualifying_line(output):
                print(f"⚠️ Disqualified intro found on attempt {attempt + 1}, regenerating...", flush=True)
                continue

            return output

        except TimeoutError:
            print("❌ Timeout during generation", flush=True)
            return None
        except Exception as e:
            print(f"❌ API error: {e}", flush=True)
            return None
    return None

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
        print(f"\n➡️ Processing record {i+1}/{len(records)}", flush=True)
        services = record.get("services", "").strip()
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
        raw_output = generate_use_cases_with_retries(prompt, retries=2)

        if raw_output:
            print(f"📝 Raw output: {raw_output}", flush=True)
            cleaned_output = postprocess_output(raw_output)
            print(f"✨ Cleaned output: {cleaned_output}", flush=True)

            if cleaned_output:
                record["use cases"] = cleaned_output
                updated += 1
                print(f"✅ Added use cases to {name}", flush=True)
            else:
                print(f"⚠️ No usable lines in output for {name}", flush=True)
        else:
            print(f"❌ Failed to generate use cases for {name}", flush=True)

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
