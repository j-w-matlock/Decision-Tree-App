import json
import uuid
import random
from typing import List, Dict, Tuple
from collections import Counter

import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Decision Tree Builder", layout="wide")

# -----------------------
# Session state bootstrap
# -----------------------
def _init_state():
    if "tree" not in st.session_state:
        st.session_state.tree = {"nodes": {}, "edges": []}
    if "sim" not in st.session_state:
        st.session_state.sim = {"active": False, "current": None, "path": []}
    if "highlight_edges" not in st.session_state:
        st.session_state.highlight_edges = []

def reset_tree():
    st.session_state.tree = {"nodes": {}, "edges": []}
    reset_sim()

def reset_sim():
    st.session_state.sim = {"active": False, "current": None, "path": []}
    st.session_state.highlight_edges = []

_init_state()

# ---------------------
# Core helpers
# ---------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:8]}"

def add_node(label: str, node_type: str) -> str:
    node_id = new_node_id()
    st.session_state.tree["nodes"][node_id] = {
        "id": node_id,
        "label": label.strip() if label else "(unnamed)",
        "type": node_type
    }
    return node_id

def edit_node(node_id: str, new_label: str, new_type: str):
    if node_id in st.session_state.tree["nodes"]:
        n = st.session_state.tree["nodes"][node_id]
        n["label"] = new_label.strip() if new_label else "(unnamed)"
        n["type"] = new_type

def delete_node(node_id: str):
    st.session_state.tree["nodes"].pop(node_id, None)
    st.session_state.tree["edges"] = [
        e for e in st.session_state.tree["edges"]
        if e["from"] != node_id and e["to"] != node_id
    ]
    reset_sim()

def add_edge(src: str, dst: str, p: float | None = None):
    if src == dst:
        st.warning("Can't create self-loop edge.")
        return
    if any(e["from"] == src and e["to"] == dst for e in st.session_state.tree["edges"]):
        st.info("Edge already exists.")
        return
    st.session_state.tree["edges"].append({"from": src, "to": dst, "p": p})

def delete_edge(index: int):
    if 0 <= index < len(st.session_state.tree["edges"]):
        st.session_state.tree["edges"].pop(index)

def outgoing(node_id: str) -> List[str]:
    return [e["to"] for e in st.session_state.tree["edges"] if e["from"] == node_id]

def outgoing_edges(node_id: str) -> List[Dict]:
    return [e for e in st.session_state.tree["edges"] if e["from"] == node_id]

def node_label(node_id: str) -> str:
    n = st.session_state.tree["nodes"].get(node_id, {"label": "?", "type": "?"})
    return f"{n['label']} ({n['type']})"

def start_sim(start_node: str):
    st.session_state.sim = {"active": True, "current": start_node, "path": [start_node]}
    st.session_state.highlight_edges = []

def step_sim(next_node: str):
    current = st.session_state.sim["current"]
    st.session_state.sim["current"] = next_node
    st.session_state.sim["path"].append(next_node)
    st.session_state.highlight_edges.append((current, next_node))

def is_terminal(node_id: str) -> bool:
    return len(outgoing(node_id)) == 0

def sanitize_prob(x) -> float | None:
    try:
        return None if x == "" else float(x)
    except:
        return None

# -----------------------
# Visualization
# -----------------------
def render_graph(highlight_edges=None, color="red"):
    G = nx.DiGraph()
    labels = {}

    for node_id, node in st.session_state.tree["nodes"].items():
        G.add_node(node_id)
        labels[node_id] = f"{node['label']} ({node['type']})"

    for edge in st.session_state.tree["edges"]:
        G.add_edge(edge["from"], edge["to"])

    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(8, 6))

    node_colors = [
        {"event": "skyblue", "response": "lightgreen", "outcome": "orange"}[
            st.session_state.tree["nodes"][n]["type"]
        ]
        for n in G.nodes()
    ]

    nx.draw(G, pos, with_labels=True, labels=labels, node_color=node_colors,
            node_size=2000, font_size=8, arrows=True, ax=ax)

    if highlight_edges:
        nx.draw_networkx_edges(G, pos, edgelist=highlight_edges, width=3, edge_color=color, ax=ax)

    st.pyplot(fig)
    plt.close(fig)

# -----------------------
# Monte Carlo
# -----------------------
def choose_next_with_probs(current: str) -> str | None:
    outs = outgoing_edges(current)
    if not outs:
        return None
    probs = [e.get("p") or 1 for e in outs]
    return random.choices([e["to"] for e in outs], weights=probs, k=1)[0]

def run_monte_carlo(start_node: str, n_runs: int, max_steps: int) -> Tuple[Counter, List[Tuple[str, str]]]:
    terminal_outcomes = Counter()
    path_counts = Counter()

    for _ in range(n_runs):
        current = start_node
        path = [current]
        for _ in range(max_steps):
            nxt = choose_next_with_probs(current)
            if nxt is None:
                break
            current = nxt
            path.append(current)
            if is_terminal(current):
                break
        terminal_outcomes[node_label(current)] += 1
        path_counts[" → ".join(node_label(n) for n in path)] += 1

    # Get the most common path and highlight its edges
    most_common_path = path_counts.most_common(1)[0][0].split(" → ")
    node_map = {node_label(k): k for k in st.session_state.tree["nodes"]}
    highlight_edges = [(node_map[most_common_path[i]], node_map[most_common_path[i + 1]])
                       for i in range(len(most_common_path) - 1)]

    return terminal_outcomes, highlight_edges

# -----------------------
# UI
# -----------------------
st.title("🌳 Decision Tree Builder with Path Highlighting")

# Reset Tree
if st.button("🔄 Reset Tree"):
    reset_tree()
    st.success("Tree reset.")

tabs = st.tabs(["Build", "Simulate", "Monte Carlo", "Import/Export"])

# -----------------------
# TAB 1: Build
# -----------------------
with tabs[0]:
    left, right = st.columns([1, 2])
    with left:
        st.header("Add Node")
        with st.form("add_node_form", clear_on_submit=True):
            node_label_in = st.text_input("Label")
            node_type_in = st.selectbox("Type", ["event", "response", "outcome"])
            if st.form_submit_button("➕ Add Node"):
                add_node(node_label_in, node_type_in)
                st.success("Node added.")
        st.header("Add Edge")
        all_nodes = list(st.session_state.tree["nodes"].keys())
        if all_nodes:
            from_node = st.selectbox("From", all_nodes, format_func=node_label)
            to_node = st.selectbox("To", all_nodes, format_func=node_label)
            p = sanitize_prob(st.text_input("Probability (optional)"))
            if st.button("➕ Add Edge"):
                add_edge(from_node, to_node, p)
        else:
            st.info("Add nodes first.")
    with right:
        st.subheader("Tree Visualization")
        render_graph()

# -----------------------
# TAB 2: Simulation
# -----------------------
with tabs[1]:
    st.header("Simulation Mode")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if all_nodes:
        if not st.session_state.sim["active"]:
            start_node = st.selectbox("Start Node", all_nodes, format_func=node_label)
            if st.button("▶️ Start Simulation"):
                start_sim(start_node)
        else:
            current = st.session_state.sim["current"]
            st.success(f"Current Node: {node_label(current)}")
            for nid in outgoing(current):
                if st.button(f"➡️ {node_label(nid)}", key=f"step_{nid}"):
                    step_sim(nid)
            if not outgoing(current):
                st.info("Reached a terminal node.")
            st.markdown("**Path so far:**")
            st.write(" → ".join(node_label(nid) for nid in st.session_state.sim["path"]))
            render_graph(st.session_state.highlight_edges)
    else:
        st.info("Add nodes to simulate.")

# -----------------------
# TAB 3: Monte Carlo
# -----------------------
with tabs[2]:
    st.header("Monte Carlo Simulation")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if all_nodes:
        start_node = st.selectbox("Start Node", all_nodes, format_func=node_label)
        n_runs = st.number_input("Number of runs", 1, 100000, 1000, 100)
        max_steps = st.number_input("Max steps per run", 1, 1000, 50)
        if st.button("▶️ Run Monte Carlo"):
            term, highlight = run_monte_carlo(start_node, n_runs, max_steps)
            st.subheader("Terminal Node Frequencies")
            df = pd.DataFrame([{"Node": k, "Count": v, "Pct": v / n_runs} for k, v in term.items()])
            st.dataframe(df, use_container_width=True)
            st.subheader("Most Probable Path Highlighted")
            render_graph(highlight, color="blue")
    else:
        st.info("Add nodes to run Monte Carlo.")

# -----------------------
# TAB 4: Import/Export
# -----------------------
with tabs[3]:
    st.header("Import/Export")
    exported = json.dumps(st.session_state.tree, indent=2)
    st.download_button("Download Tree JSON", data=exported, file_name="decision_tree.json")
    uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
    if uploaded:
        raw = json.load(uploaded)
        if "nodes" in raw and "edges" in raw:
            st.session_state.tree = raw
            reset_sim()
            st.success("Tree imported.")
        else:
            st.error("Invalid JSON format.")
