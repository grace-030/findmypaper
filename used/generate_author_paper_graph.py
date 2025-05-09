import pandas as pd
import json
import re
import os
from collections import defaultdict
import networkx as nx

# ====== category ======
category_map = {
    "cs": "Computer Science",
    "math": "Mathematics",
    "physics": "Physics",
    "q-bio": "Quantitative Biology",
    "q-fin": "Quantitative Finance",
    "stat": "Statistics",
    "eess": "Electrical Engineering",
    "econ": "Economics"
}

def map_category(cat):
    for key in category_map:
        if key in cat:
            return category_map[key]
    return "Other"

def extract_year(paper_id):
    try:
        match = re.match(r'.*/(\d{2})(\d{2})(\d{2})', paper_id)
        if match:
            year = int(match.group(1))
            return 1900 + year if year > 50 else 2000 + year
    except:
        return None
    return None

def is_valid_author(author):
    invalid_keywords = [
        "University", "Institute", "Laboratory", "Dept", "Department",
        "Collaboration", "College", "Group", "Center", "School",
        "Russia", "Germany", "France", "China", "Japan", "USA",
        "Poland", "Italy", "Turkey", "Argentina", "Korea", "India",
        "UK", "Netherlands", "Mexico"
    ]
    return len(author) > 2 and not any(kw in author for kw in invalid_keywords)

# ====== path======
folder_path = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(folder_path, "arxiv.csv")


print("📥 Loading CSV...")
df = pd.read_csv(csv_path)

nodes = []
links = []
paper_ids = set()
author_nodes = {}
author_paper_count = defaultdict(int)
paper_citation_count = defaultdict(int)
paper_authors_map = defaultdict(list)

# ====== handle each row ======
for _, row in df.iterrows():
    paper_id = row["id"]
    title = str(row["title"]).strip()
    category = map_category(str(row.get("categories", "")))
    year = extract_year(paper_id)
    authors_raw = str(row.get("authors", "")).replace("\n", " ").split(",")

    if year is None:
        continue

    clean_authors = [a.strip() for a in authors_raw if is_valid_author(a.strip())]

    if paper_id not in paper_ids:
        paper_node = {
            "id": paper_id,
            "label": title,
            "type": "paper",
            "category": category,
            "year": year,
            "pagerank": 0.0,
            "citation_count": 0,
            "author_list": clean_authors
        }
        nodes.append(paper_node)
        paper_ids.add(paper_id)
        paper_authors_map[paper_id] = clean_authors

    for author in clean_authors:
        author_id = "author:" + author
        author_paper_count[author_id] += 1

        if author_id not in author_nodes:
            author_nodes[author_id] = {
                "id": author_id,
                "label": author,
                "type": "author",
                "paper_count": 0,
                "pagerank": 0.0,
                "coauthors": 0
            }

        links.append({
            "source": author_id,
            "target": paper_id,
            "weight": 1
        })

# ====== count======
for aid, count in author_paper_count.items():
    author_nodes[aid]["paper_count"] = count

for paper_id, authors in paper_authors_map.items():
    for a1 in authors:
        for a2 in authors:
            if a1 != a2:
                author_nodes["author:" + a1]["coauthors"] += 1

# ====== Citation count  ======
if "citations" in df.columns:
    for _, row in df.iterrows():
        citing = row.get("citations", "")
        import ast

if "citations" in df.columns:
    for _, row in df.iterrows():
        citing = row.get("citations", "")
        try:
            citing_list = ast.literal_eval(citing)
            if isinstance(citing_list, list):
                for cited_id in citing_list:
                    if cited_id in paper_ids:
                        paper_citation_count[cited_id] += 1
        except:
            continue 

        for cited_id in citing_list:
            if cited_id in paper_ids:
                paper_citation_count[cited_id] += 1

    for n in nodes:
        if n["type"] == "paper":
            n["citation_count"] = paper_citation_count.get(n["id"], 0)

# ====== combine nodes ======
nodes += list(author_nodes.values())

# ====== PageRank ======
G = nx.DiGraph()
for link in links:
    G.add_edge(link["source"], link["target"])

print("⚙️ Calculating PageRank...")
pagerank_dict = nx.pagerank(G, alpha=0.85)
for node in nodes:
    node["pagerank"] = round(pagerank_dict.get(node["id"], 0), 6)

# delete isolated author
linked_authors = set(l["source"] for l in links)
nodes = [n for n in nodes if n["type"] == "paper" or n["id"] in linked_authors]

# ======  JSON ======
print("💾 Saving full graph...")
with open(os.path.join(folder_path, "author_paper_graph_final.json"), "w") as f:
    json.dump({"nodes": nodes, "links": links}, f, indent=2)

# ====== subset ======
subset_limit = 5000

paper_nodes = [n for n in nodes if n["type"] == "paper"][:subset_limit]
paper_ids = set(n["id"] for n in paper_nodes)

linked_author_ids = set(l["source"] for l in links if l["target"] in paper_ids)

subset_node_ids = paper_ids.union(linked_author_ids)
subset_nodes = [n for n in nodes if n["id"] in subset_node_ids]
subset_links = [l for l in links if l["source"] in subset_node_ids and l["target"] in subset_node_ids]

with open(os.path.join(folder_path, "author_paper_graph_10k.json"), "w") as f:
    json.dump({"nodes": subset_nodes, "links": subset_links}, f, indent=2)

print("✅ Saved subset graph to author_paper_graph_10k.json")
