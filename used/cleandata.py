import os
import json

# Input and output directories
input_dir = "datafiles"
output_dir = "datafiles_cleaned"
os.makedirs(output_dir, exist_ok=True)

# Fields to keep, including update_date
fields_to_keep = ["id", "submitter", "authors", "title", "categories", "abstract", "update_date"]

# Loop through each metadata_part_*.json file
for filename in os.listdir(input_dir):
    if filename.startswith("metadata_part_") and filename.endswith(".json"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        cleaned_nodes = []

        with open(input_path, "r", encoding="utf-8") as infile:
            for line in infile:
                try:
                    record = json.loads(line)
                    cleaned = {field: record.get(field, "") for field in fields_to_keep}
                    if isinstance(cleaned["abstract"], str):
                        cleaned["abstract"] = cleaned["abstract"].strip()
                    cleaned_nodes.append(cleaned)
                except json.JSONDecodeError:
                    continue  # skip malformed lines

        # Save cleaned records in required format
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump({"nodes": cleaned_nodes}, outfile, indent=2)

print("✅ All files cleaned and saved to 'datafiles_cleaned/'")