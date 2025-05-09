import os
import json

# Parameters
input_path = "metadata.json"  # The original file
output_dir = "datafiles"      # Output folder
num_files = 30                # Number of output files

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# First, count total lines (records)
with open(input_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

total_lines = len(lines)
chunk_size = (total_lines + num_files - 1) // num_files  # Round up division

# Split and save
for i in range(num_files):
    chunk = lines[i * chunk_size : (i + 1) * chunk_size]
    output_path = os.path.join(output_dir, f"metadata_part_{i+1}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for line in chunk:
            try:
                json_obj = json.loads(line)  # Validate JSON
                f_out.write(json.dumps(json_obj) + '\n')
            except json.JSONDecodeError:
                continue  # Skip invalid JSON lines

print(f"Done. {num_files} files saved in the '{output_dir}' directory.")
