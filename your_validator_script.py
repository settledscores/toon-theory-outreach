import json

INPUT_PATH = "leads/scraped_leads.ndjson"


def read_and_validate_multiline_ndjson(path):
    valid_records = []
    buffer = ""
    block_number = 0
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            buffer += line
            if line.strip() == "}":
                block_number += 1
                try:
                    record = json.loads(buffer)
                    valid_records.append(record)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error at block #{block_number} (line {line_num}): {e}")
                    print("\n--- Start of problem block ---")
                    print(buffer.strip().splitlines()[0])
                    print("...")
                    print(buffer.strip().splitlines()[-1])
                    print("--- End of problem block ---\n")
                buffer = ""
    print(f"✅ Loaded {len(valid_records)} valid records")
    return valid_records


if __name__ == "__main__":
    read_and_validate_multiline_ndjson(INPUT_PATH)
