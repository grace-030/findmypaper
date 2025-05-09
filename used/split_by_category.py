import os
import json
from collections import defaultdict

# Define input and output directories
input_dir = "datafiles_cleaned"
output_dir = "datafiles_categories"
os.makedirs(output_dir, exist_ok=True)

# Category mapping (prefix to main category)
prefix_to_category = {
    "astro-ph": "physics", "cond-mat": "physics", "gr-qc": "physics", "hep-ex": "physics",
    "hep-lat": "physics", "hep-ph": "physics", "hep-th": "physics", "math-ph": "physics",
    "nlin": "physics", "nucl-ex": "physics", "nucl-th": "physics", "physics": "physics", "quant-ph": "physics",
    "math": "mathematics",
    "cs": "computer_science",
    "q-bio": "quantitative_biology",
    "q-fin": "quantitative_finance",
    "stat": "statistics",
    "eess": "electrical_engineering",
    "econ": "economics"
}

# Prepare a dictionary for storing categorized papers
categorized_papers = defaultdict(list)

# Process all metadata_part_X.json files
for i in range(1, 31):
    filename = f"metadata_part_{i}.json"
    filepath = os.path.join(input_dir, filename)
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for paper in data.get("nodes", []):
            categories = paper.get("categories", "")
            prefixes = {cat.split(".")[0] for cat in categories.split()}
            assigned = set()
            for prefix in prefixes:
                main_category = prefix_to_category.get(prefix)
                if main_category and main_category not in assigned:
                    categorized_papers[main_category].append(paper)
                    assigned.add(main_category)

# Save each category to its own JSON file
for category, papers in categorized_papers.items():
    out_path = os.path.join(output_dir, f"{category}.json")
    with open(out_path, "w", encoding="utf-8") as out_file:
        json.dump({"nodes": papers}, out_file, indent=2)

print("✅ Papers successfully categorized into datafiles_categories/")