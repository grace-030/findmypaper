import pandas as pd
import json
from collections import defaultdict, Counter
import networkx as nx


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


csv_path = "arxiv.csv"
output_path = "coauthor_graph.json"

# ====== clean data ======
df = pd.read_csv(csv_path)
df = df.head(5000)

nodes = {}
edges = defaultdict(lambda: {"weight": 0, "papers": [], "titles": [], "category": None})
author_cat_counter = defaultdict(list)
G = nx.Graph()

for _, row in df.iterrows():
    paper_id = row["id"]
    category_raw = str(row.get("categories", ""))
    category = map_category(category_raw)
    title = str(row.get("title", "")).strip()

    try:
        authors_parsed = eval(row.get("authors_parsed", "[]"))
        author_names = [" ".join(a[:2]).strip() for a in authors_parsed if len(a) >= 2]
    except:
        continue

    for author in author_names:
        author_id = f"author:{author}"
        if author_id not in nodes:
            nodes[author_id] = {
                "id": author_id,
                "label": author,
                "type": "author",
                "paper_count": 0
            }
        nodes[author_id]["paper_count"] += 1
        author_cat_counter[author_id].append(category)

    for i in range(len(author_names)):
        for j in range(i + 1, len(author_names)):
            a1 = f"author:{author_names[i]}"
            a2 = f"author:{author_names[j]}"
            key = tuple(sorted([a1, a2]))
            edges[key]["weight"] += 1
            edges[key]["papers"].append(paper_id)
            edges[key]["titles"].append(title)
            edges[key]["category"] = category
            G.add_edge(a1, a2, weight=edges[key]["weight"])

# ====== pagerank ======
pagerank_scores = nx.pagerank(G, alpha=0.85)
degree_dict = dict(G.degree())
betweenness_dict = nx.betweenness_centrality(G)
closeness_dict = nx.closeness_centrality(G)

for node_id in nodes:
    cat_list = author_cat_counter.get(node_id, [])
    nodes[node_id]["category"] = Counter(cat_list).most_common(1)[0][0] if cat_list else "Other"
    nodes[node_id]["pagerank"] = round(pagerank_scores.get(node_id, 0), 6)
    nodes[node_id]["degree"] = degree_dict.get(node_id, 0)
    nodes[node_id]["betweenness"] = round(betweenness_dict.get(node_id, 0), 6)
    nodes[node_id]["closeness"] = round(closeness_dict.get(node_id, 0), 6)
    nodes[node_id]["coauthor_count"] = degree_dict.get(node_id, 0)

# ====== get JSON ======
graph = {
    "nodes": list(nodes.values()),
    "links": [
        {
            "source": a,
            "target": b,
            "weight": data["weight"],
            "papers": data["papers"],
            "titles": data["titles"],
            "category": data["category"]
        }
        for (a, b), data in edges.items()
    ]
}

with open(output_path, "w") as f:
    json.dump(graph, f, indent=2)

print("✅ coauthor_graph.json saved，including PageRank、Degree、Betweenness、Closeness、Category")
