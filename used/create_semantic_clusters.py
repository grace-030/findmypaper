import pandas as pd
import networkx as nx
import os
from collections import defaultdict, Counter
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")  # light and fast

# Load data
df = pd.read_csv("arxiv_paper_nodes.csv")
df = df.drop_duplicates(subset="id")
df["categories"] = df["categories"].fillna("").apply(lambda x: x.strip().split())

# Build category → paper_id mapping
category_papers = defaultdict(set)
for _, row in df.iterrows():
    for cat in row["categories"]:
        category_papers[cat].add(row["id"])

# Build citation map
paper_id_set = set(df["id"])
citation_map = {}
for _, row in df.iterrows():
    pid = row["id"]
    try:
        citations = eval(row["citations"]) if isinstance(row["citations"], str) else []
    except:
        citations = []
    citation_map[pid] = [c for c in citations if c in paper_id_set]

id_to_row = df.set_index("id").to_dict("index")

# Helper to extract top 3 TF-IDF keywords from a list of abstracts
def extract_keywords(texts, top_k=3):
    if not texts:
        return "None"
    tfidf = TfidfVectorizer(stop_words="english", max_features=100)
    X = tfidf.fit_transform(texts)
    scores = X.sum(axis=0).A1
    idxs = scores.argsort()[-top_k:][::-1]
    return ", ".join([tfidf.get_feature_names_out()[i] for i in idxs])

# Process each category
for category, paper_ids in category_papers.items():
    print(f"\n📚 Processing category: {category}")

    # Build graph
    G = nx.DiGraph()
    for pid in paper_ids:
        G.add_node(pid)
        for cited in citation_map.get(pid, []):
            if cited in paper_ids:
                G.add_edge(cited, pid)

    # Skip if too small
    if G.number_of_nodes() < 20:
        continue

    # Compute PageRank
    try:
        pr = nx.pagerank(G)
    except:
        continue

    top_papers = sorted(paper_ids, key=lambda pid: pr.get(pid, 0), reverse=True)[:100]
    top_papers = [pid for pid in top_papers if pid in id_to_row and pd.notnull(id_to_row[pid]["abstract"])]

    if len(top_papers) < 10:
        continue

    # Embeddings
    abstracts = [id_to_row[pid]["abstract"] for pid in top_papers]
    embeddings = model.encode(abstracts)

    # Clustering
    k = 10
    kmeans = KMeans(n_clusters=k, random_state=42)
    cluster_ids = kmeans.fit_predict(embeddings)

    # Assign cluster
    cluster_texts = defaultdict(list)
    paper_cluster = {}
    for pid, cid, abstract in zip(top_papers, cluster_ids, abstracts):
        paper_cluster[pid] = cid
        cluster_texts[cid].append(abstract)

    # Extract top 3 keywords per cluster
    cluster_keywords = {cid: extract_keywords(texts) for cid, texts in cluster_texts.items()}

    # Write nodes.csv
    nodes = []
    for pid in top_papers:
        row = id_to_row[pid]
        nodes.append({
            "id": pid,
            "title": row["title"],
            "pagerank": pr.get(pid, 0),
            "abstract": row["abstract"],
            "cluster": paper_cluster[pid],
            "keywords": cluster_keywords[paper_cluster[pid]]
        })

    # Induce edge list among top papers
    edges = []
    for pid in top_papers:
        for cited in citation_map.get(pid, []):
            if cited in top_papers:
                edges.append({"source": cited, "target": pid})

    # Save
    out_dir = os.path.join("semantic_clusters", category)
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(nodes).to_csv(os.path.join(out_dir, "nodes.csv"), index=False)
    pd.DataFrame(edges).to_csv(os.path.join(out_dir, "edges.csv"), index=False)

print("\n✅ Semantic clusters saved under semantic_clusters/{category}/")