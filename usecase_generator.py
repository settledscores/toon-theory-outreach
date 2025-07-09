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
    return f"""Based on the company’s services below, list 3 *practical, clear, and benefit-focused* use cases for an explainer video that could help them communicate better with customers.

Each bullet must:
- Be short (under 20 words)
- Sound natural and human — no corporate speak or generic phrasing
- Be specific to the actual service or customer benefit
- Do NOT start with generic verbs like "Explaining", "Clarifying", or "Walking through"
- Should sound like one of the examples below

Format the result as a single line with items separated by "|"

Examples of good use cases:
- Showing how a Fractional CFO can boost profits in 90 seconds
- Walking founders through their cash runway without a single spreadsheet
- Visualizing how mediation saves 4+ months of legal delays
- Framing estate planning as peace-of-mind, not paperwork
- Mapping the client journey for your fitness coaching program
- Turning your offer into a story — not a sales pitch
- Bringing your KPI dashboard to life with 2-minute visuals
- Outlining your onboarding steps without those boring emails
- Pitching your legal-writing service without industry jargon

Services:
{services}
"""

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

def postprocess_output(text):
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        original = line.strip()
        if not original:
            continue
        if any(re.match(p, original) for p in bad_line_patterns):
            print(f"⚠️ Disqualified by regex: {original}", flush=True)
            continue
        cleaned.append(original)
    return " | ".join(cleaned)

def main():
    print("🎬 Generating use cases from services...\n", flush=True)

    try:
        records = read_multiline_ndjson(INPUT_PATH)
    except Exception as e:
        print(f"❌ Failed to load NDJSON: {e}", flush=True)
        return

    updated = 0
    results = []

    for i, record in enumerate(records):
        print(f"\n➡️ Record {i+1}/{len(records)}", flush=True)
        services = record.get("services", "").strip()
        name = record.get("business name", "[no name]")
        website = record.get("website url", "[no website]")
        use_cases = record.get("use cases", None)

        if not services:
            print(f"⚠️ No services for {name}, skipping", flush=True)
            results.append(record)
            continue

        if use_cases is not None and use_cases.strip():
            print(f"ℹ️ Skipping {name} — already filled: {use_cases!r}", flush=True)
            results.append(record)
            continue

        print(f"🔍 Generating use cases for: {name} ({website})", flush=True)

        prompt = generate_prompt(truncate_text(services))
        print("\n📝 Prompt:\n" + "-" * 40 + f"\n{prompt}\n" + "-" * 40, flush=True)

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
            print("\n📤 Raw model output:\n" + "-" * 40 + f"\n{raw_output}\n" + "-" * 40, flush=True)

            cleaned_output = postprocess_output(raw_output)
            print(f"\n✅ Cleaned use cases: {cleaned_output}\n", flush=True)

            record["use cases"] = cleaned_output
            updated += 1

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
