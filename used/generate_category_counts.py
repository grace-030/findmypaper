import os
import json
from collections import defaultdict

input_dir = "datafiles_cleaned"
output_file = "categories.json"

prefix_to_main_category = {
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

# Initialize counters
category_counts = defaultdict(int)
category_years = defaultdict(lambda: defaultdict(int))
total_paper_count = 0

# Parse each cleaned data file
for file in os.listdir(input_dir):
    if file.endswith(".json"):
        with open(os.path.join(input_dir, file), "r", encoding="utf-8") as f:
            data = json.load(f)
            for node in data.get("nodes", []):
                total_paper_count += 1
                seen_main_cats = set()
                raw_cats = node.get("categories", "")
                update_date = node.get("update_date", "")[:4]  # e.g. "2007" from "2007-08-12"

                for cat in raw_cats.split():
                    prefix = cat.split(".")[0]
                    main_cat = prefix_to_main_category.get(prefix)
                    if main_cat and main_cat not in seen_main_cats:
                        category_counts[main_cat] += 1
                        if update_date.isdigit():
                            category_years[main_cat][update_date] += 1
                        seen_main_cats.add(main_cat)

# Build final output
final_output = {}
for cat in sorted(category_counts):
    count = category_counts[cat]
    percent = (count / total_paper_count * 100) if total_paper_count > 0 else 0
    yearly = category_years[cat]
    sorted_yearly = dict(sorted(yearly.items(), key=lambda x: int(x[0])))
    final_output[cat] = {
        "count": count,
        "percentage": round(percent, 2),
        "years": sorted_yearly
    }

# Write to file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2)

print("✅ categories.json updated with count, percentage, and per-year breakdown.")