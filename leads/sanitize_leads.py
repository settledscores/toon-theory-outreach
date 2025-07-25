import json

INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/sanitized_leads.ndjson"

def sanitize_ndjson(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "website url" in data:
                    sanitized = {"website url": data["website url"]}
                    outfile.write(json.dumps(sanitized, ensure_ascii=False) + "\n")
            except json.JSONDecodeError:
                print("Skipping invalid JSON line:", line)

if __name__ == "__main__":
    sanitize_ndjson(INPUT_PATH, OUTPUT_PATH)
