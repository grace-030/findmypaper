from flask import Flask, jsonify, send_from_directory, render_template, request
from flask_cors import CORS
import pandas as pd
import json
import os
import ast

app = Flask(__name__)
PAGE_SIZE = 50
DATA_DIR = "datafiles_categories"
CSV_DIR = "datafiles"
CORS(app)

CATEGORIES = {
    "computer_science": "computer_science.json",
    "physics": "physics.json",
    "mathematics": "mathematics.json",
    "quantitative_biology": "quantitative_biology.json",
    "quantitative_finance": "quantitative_finance.json",
    "statistics": "statistics.json",
    "electrical_engineering": "electrical_engineering.json",
    "economics": "economics.json"
}

# ---------- Static HTML Page Routes ---------- #

@app.route("/")
def menu():
    return render_template("index.html")

@app.route("/visualization")
def visualization():
    return render_template("visualization.html")

@app.route("/author_paper")
def author_paper():
    return render_template("author_paper_graph.html")

@app.route("/citation")
def citation():
    return render_template("citation.html")

@app.route("/coauthor_graph")
def coauthor_graph():
    return render_template("coauthor_graph.html")

@app.route("/coauthor_3d")
def coauthor_3d():
    return render_template("coauthor_3d.html")

@app.route('/api/graph_data')
def get_graph_data():
    return jsonify(load_data())

@app.route('/api/coauthor_graph_data')
def get_coauthor_graph_data():
    return jsonify(load_coauthor_data())

@app.route('/api/citation_graph_data')
def get_citation_graph_data():
    return jsonify(load_citation_data())

@app.route('/graphdata/<path:filename>')
def serve_graphdata(filename):
    return send_from_directory('graphdata', filename)

@app.route('/semantic_clusters/<path:filename>')
def serve_semantic_clusters(filename):
    return send_from_directory('semantic_clusters', filename)

# ---------- Category HTML Page Routes ---------- #

@app.route("/<category>")
def category_page(category):
    if category in CATEGORIES:
        return render_template(f"{category}.html")
    return "Category not found", 404

# ---------- Paginated API Routes for Each Category ---------- #

@app.route("/api/<category>")
def category_api(category):
    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category"}), 404

    filepath = os.path.join(DATA_DIR, CATEGORIES[category])
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
        papers = data.get("nodes", [])

    page = int(request.args.get("page", 1))
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    total_pages = (len(papers) + PAGE_SIZE - 1) // PAGE_SIZE

    return jsonify({
        "page": page,
        "total_pages": total_pages,
        "papers": papers[start:end]
    })

# ---------- Load Graph Data from CSV ---------- #

def load_data():
    file_path = os.path.join(CSV_DIR, 'arxiv.csv')
    df = pd.read_csv(file_path).head(10000)

    nodes = []
    links = []
    paper_id_map = {}

    for i, row in df.iterrows():
        paper_id = row['id']
        title = row['title']
        category = row['categories']

        paper_node = {
            'id': paper_id,
            'label': title,
            'type': 'paper',
            'category': category
        }
        nodes.append(paper_node)
        paper_id_map[paper_id] = paper_node

        authors = str(row['authors']).split(',')[:3]
        for author in authors:
            author = author.strip()
            author_node_id = f'author:{author}'
            if not any(n['id'] == author_node_id for n in nodes):
                nodes.append({
                    'id': author_node_id,
                    'label': author,
                    'type': 'author'
                })
            links.append({
                'source': author_node_id,
                'target': paper_id
            })

    return {'nodes': nodes, 'links': links}

def load_coauthor_data():
    file_path = os.path.join(CSV_DIR, 'arxiv.csv')
    df = pd.read_csv(file_path).head(10000)

    links = []
    nodes = {}

    for _, row in df.iterrows():
        authors = str(row['authors']).split(',')
        authors = [a.strip() for a in authors[:5]]

        for author in authors:
            if author not in nodes:
                nodes[author] = {
                    'id': f'author:{author}',
                    'label': author,
                    'type': 'author'
                }

        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                links.append({
                    'source': f'author:{authors[i]}',
                    'target': f'author:{authors[j]}'
                })

    return {'nodes': list(nodes.values()), 'links': links}

def load_citation_data():
    file_path = os.path.join(CSV_DIR, 'arxiv.csv')
    df = pd.read_csv(file_path).head(10000)

    nodes = {}
    links = []

    for _, row in df.iterrows():
        paper_id = row['id']
        title = row['title']
        category = row['categories']
        nodes[paper_id] = {
            'id': paper_id,
            'label': title,
            'type': 'paper',
            'category': category
        }

    for _, row in df.iterrows():
        if 'citations' in df.columns and pd.notna(row['citations']):
            try:
                cited_ids = ast.literal_eval(row['citations'])
                for cited in cited_ids:
                    if cited in nodes:
                        links.append({
                            'source': row['id'],
                            'target': cited
                        })
            except Exception as e:
                print(f"Error parsing citations for {row['id']}: {e}")

    return {'nodes': list(nodes.values()), 'links': links}

# ---------- Run the App ---------- #

if __name__ == "__main__":
    app.run(debug=True)