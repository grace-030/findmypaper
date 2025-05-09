import json

# Load full graph
with open("graph.json", "r") as f:
    full_graph = json.load(f)

# How many top nodes to keep
TOP_N = 10000

# Sort and take top N nodes by PageRank
top_nodes = sorted(full_graph["nodes"], key=lambda n: -n.get("pagerank", 0))[:TOP_N]
top_node_ids = {node["id"] for node in top_nodes}

# Filter links: both source and target must be in top_node_ids
filtered_links = [
    link for link in full_graph["links"]
    if link["source"] in top_node_ids and link["target"] in top_node_ids
]

# Final subgraph
subgraph = {
    "nodes": top_nodes,
    "links": filtered_links
}

# Save subgraph to new JSON file
with open("sample_graph.json", "w") as f:
    json.dump(subgraph, f, indent=2)

print(f"✅ Extracted {len(top_nodes)} nodes and {len(filtered_links)} links into sample_graph.json")