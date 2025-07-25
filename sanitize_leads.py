import json

INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/sanitized_leads.ndjson"

def sanitize_multiline_ndjson(input_path, output_path):
    buffer = ""
    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue
            buffer += stripped
            if stripped.endswith("}"):
                try:
                    obj = json.loads(buffer)
                    if "website url" in obj:
                        only_website = {"website url": obj["website url"]}
                        outfile.write(json.dumps(only_website, ensure_ascii=False) + "\n")
                except json.JSONDecodeError:
                    print("Skipping invalid JSON block:\n", buffer)
                buffer = ""

if __name__ == "__main__":
    sanitize_multiline_ndjson(INPUT_PATH, OUTPUT_PATH)
