import pandas as pd
from itertools import product
from collections import defaultdict
import os
import networkx as nx

# Load input data
papers_df = pd.read_csv("arxiv_paper_nodes.csv")
mapping_df = pd.read_csv("arxiv_category_mapping_cs_fixed.csv")

# Mapping: category → (field, subfield)
category_to_field = dict(zip(mapping_df["category"], mapping_df["field"]))
category_to_subfield = dict(zip(mapping_df["category"], mapping_df["subfield"]))

# Paper → fields/subfields
paper_to_fields = {}
paper_to_subfields = {}
field_subfields = defaultdict(set)
subfield_papers = defaultdict(set)

for _, row in papers_df.iterrows():
    paper_id = row["id"]
    cats = str(row["categories"]).split()

    fields = set()
    subfields = set()
    for cat in cats:
        f = category_to_field.get(cat)
        sf = category_to_subfield.get(cat)
        if f and sf:
            fields.add(f)
            subfields.add(sf)
            field_subfields[f].add(sf)
            subfield_papers[sf].add(paper_id)

    paper_to_fields[paper_id] = fields
    paper_to_subfields[paper_id] = subfields

# Edge counts
field_edges = defaultdict(lambda: defaultdict(int))

for _, row in papers_df.iterrows():
    target_id = row["id"]
    target_fields = paper_to_fields.get(target_id, set())
    target_subfields = paper_to_subfields.get(target_id, set())

    citations = row["citations"]
    if isinstance(citations, str) and citations.startswith("["):
        try:
            citations = eval(citations)
        except:
            citations = []
    elif not isinstance(citations, list):
        citations = []

    for cited_id in citations:
        source_fields = paper_to_fields.get(cited_id, set())
        source_subfields = paper_to_subfields.get(cited_id, set())
        common_fields = target_fields & source_fields

        for field in common_fields:
            valid_subs = field_subfields[field]
            for src, tgt in product(source_subfields, target_subfields):
                if src in valid_subs and tgt in valid_subs:
                    field_edges[field][(src, tgt)] += 1

# Write per field
for field, edge_counts in field_edges.items():
    valid_subs = field_subfields[field]
    subfield_sizes = {sf: len(subfield_papers[sf]) for sf in valid_subs}
    subfield_sizes = {sf: sz for sf, sz in subfield_sizes.items() if sz > 0}
    valid_nodes = set(subfield_sizes)

    edge_records = []
    G = nx.DiGraph()

    for (src, tgt), raw_count in edge_counts.items():
        if src in valid_nodes and tgt in valid_nodes:
            M, N = subfield_sizes[src], subfield_sizes[tgt]
            weight = raw_count / (M * N) if M > 0 and N > 0 else 0
            G.add_edge(src, tgt, weight=weight)
            edge_records.append({
                "source": src,
                "target": tgt,
                "weight": weight,
                "raw_count": raw_count
            })

    # Create DataFrames
    edge_df = pd.DataFrame(edge_records).dropna(subset=["source", "target"])
    used_nodes = set(edge_df["source"]).union(set(edge_df["target"]))
    pagerank = nx.pagerank(G, weight="weight")

    node_data = [{
        "id": sf,
        "paper_count": subfield_sizes[sf],
        "pagerank": pagerank.get(sf, 0)
    } for sf in used_nodes]

    # Save
    dir_path = f"graphdata/{field.replace('/', '_')}"
    os.makedirs(dir_path, exist_ok=True)
    pd.DataFrame(node_data).to_csv(f"{dir_path}/nodes.csv", index=False)
    edge_df.to_csv(f"{dir_path}/edges.csv", index=False)

print("✅ Subfield graphs regenerated with empty source/target edges removed.")
