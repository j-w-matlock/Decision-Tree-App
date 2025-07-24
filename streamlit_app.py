import json
import uuid
import random
from typing import List, Dict, Tuple
from collections import Counter, deque
import io

import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Decision Tree Builder", layout="wide")

# -----------------------------------------------------------------------------
# Session state bootstrap
# -----------------------------------------------------------------------------
def _init_state():
    if "tree" not in st.session_state:
        st.session_state.tree = {"nodes": {}, "edges": []}
    if "sim" not in st.session_state:
        st.session_state.sim = {"active": False, "current": None, "path": []}
    if "highlight_edges" not in st.session_state:
        st.session_state.highlight_edges = []
    if "history" not in st.session_state:
        st.session_state.history = deque(maxlen=20)  # for undo
    if "redo_stack" not in st.session_state:
        st.session_state.redo_stack = deque(maxlen=20)

def save_history():
    st.session_state.history.append(json.dumps(st.session_state.tree))
    st.session_state.redo_stack.clear()

def undo():
    if st.session_state.history:
        st.session_state.redo_stack.append(json.dumps(st.session_state.tree))
        st.session_state.tree = json.loads(st.session_state.history.pop())

def redo():
    if st.session_state.redo_stack:
        st.session_state.history.append(json.dumps(st.session_state.tree))
        st.session_state.tree = json.loads(st.session_state.redo_stack.pop())

def reset_tree():
    save_history()
    st.session_state.tree = {"nodes": {}, "edges": []}
    reset_sim()

def reset_sim():
    st.session_state.sim = {"active": False, "current": None, "path": []}
    st.session_state.highlight_edges = []

_init_state()

# -----------------------------------------------------------------------------
# Core helpers
# -----------------------------------------------------------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:8]}"

def add_node(label: str, node_type: str) -> str:
    save_history()
    node_id = new_node_id()
    st.session_state.tree["nodes"][node_id] = {
        "id": node_id,
        "label": label.strip() if label else "(unnamed)",
        "type": node_type
    }
    return node_id

def edit_node(node_id: str, new_label: str, new_type: str):
    save_history()
    if node_id in st.session_state.tree["nodes"]:
        n = st.session_state.tree["nodes"][node_id]
        n["label"] = new_label.strip() if new_label else "(unnamed)"
        n["type"] = new_type

def delete_node(node_id: str):
    save_history()
    st.session_state.tree["nodes"].pop(node_id, None)
    st.session_state.tree["edges"] = [
        e for e in st.session_state.tree["edges"]
        if e["from"] != node_id and e["to"] != node_id
    ]
    reset_sim()

def add_edge(src: str, dst: str, p: float | None = None):
    save_history()
    if src == dst:
        st.warning("Can't create self-loop edge.")
        return
    if any(e["from"] == src and e["to"] == dst for e in st.session_state.tree["edges"]):
        st.info("Edge already exists.")
        return
    st.session_state.tree["edges"].append({"from": src, "to": dst, "p": p})

def delete_edge(index: int):
    save_history()
    if 0 <= index < len(st.session_state.tree["edges"]):
        st.session_state.tree["edges"].pop(index)

def outgoing(node_id: str) -> List[str]:
    return [e["to"] for e in st.session_state.tree["edges"] if e["from"] == node_id]

def outgoing_edges(node_id: str) -> List[Dict]:
    return [e for e in st.session_state.tree["edges"] if e["from"] == node_id]

def node_label(node_id: str) -> str:
    n = st.session_state.tree["nodes"].get(node_id, {"label": "?", "type": "?"})
    return f"{n['label']} ({n['type']})"

def sanitize_prob(x) -> float | None:
    try:
        return None if x == "" else float(x)
    except:
        return None

# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------
def render_graph(highlight_edges=None, colors=None):
    """Draw the current decision graph."""
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

    nx.draw(
        G, pos,
        with_labels=True,
        labels=labels,
        node_color=node_colors,
        node_size=2000,
        font_size=8,
        arrows=True,
        ax=ax
    )

    # Highlight edges with color gradient if provided
    if highlight_edges:
        if not colors:
            colors = ["red"] * len(highlight_edges)
        nx.draw_networkx_edges(
            G, pos, edgelist=highlight_edges, width=3, edge_color=colors, ax=ax
        )

    st.pyplot(fig)
    plt.close(fig)

# -----------------------------------------------------------------------------
# Monte Carlo
# -----------------------------------------------------------------------------
def choose_next_with_probs(current: str) -> str | None:
    outs = outgoing_edges(current)
    if not outs:
        return None
    probs = [e.get("p") or 1 for e in outs]
    return random.choices([e["to"] for e in outs], weights=probs, k=1)[0]

def run_monte_carlo(start_node: str, n_runs: int, max_steps: int) -> Tuple[Counter, List[Tuple[str, str]], Counter]:
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

    # Build highlight for top 3 paths
    top_paths = [p.split(" → ") for p, _ in path_counts.most_common(3)]
    highlight_edges, colors = [], []
    color_map = ["blue", "purple", "green"]
    node_map = {node_label(k): k for k in st.session_state.tree["nodes"]}
    for i, path in enumerate(top_paths):
        for j in range(len(path) - 1):
            highlight_edges.append((node_map[path[j]], node_map[path[j + 1]]))
            colors.append(color_map[i % len(color_map)])

    return terminal_outcomes, (highlight_edges, colors), path_counts

# -----------------------------------------------------------------------------
# Export to Excel
# -----------------------------------------------------------------------------
def export_monte_carlo_to_excel(term: Counter, path_counts: Counter, n_runs: int):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([{"Node": k, "Count": v, "Pct": v / n_runs} for k, v in term.items()])\
            .to_excel(writer, sheet_name="Terminal Frequencies", index=False)
        pd.DataFrame([{"Path": p, "Count": c, "Pct": c / n_runs} for p, c in path_counts.most_common(50)])\
            .to_excel(writer, sheet_name="Top Paths", index=False)
    return output.getvalue()

# -----------------------------------------------------------------------------
# Simulation Helpers
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.title("🌳 Decision Tree Builder — Polished Edition")

# Undo / Redo
undo_col, redo_col = st.columns([0.2, 0.2])
if undo_col.button("↩ Undo", help="Revert the most recent change."):
    undo()
if redo_col.button("↪ Redo", help="Reapply a reverted change."):
    redo()

tabs = st.tabs(["Build", "Simulate", "Monte Carlo", "Import / Export"])

# ---------------------
# TAB 1: Build
# ---------------------
with tabs[0]:
    st.header("Build Your Tree")
    all_nodes = list(st.session_state.tree["nodes"].keys())

    with st.form("add_node_form", clear_on_submit=True):
        node_label_in = st.text_input("Node label", help="Enter a name for this node.")
        node_type_in = st.selectbox("Node type", ["event", "response", "outcome"], help="Select the type of node.")
        if st.form_submit_button("➕ Add Node"):
            add_node(node_label_in, node_type_in)
            st.success("Node added.")

    # Probability validation
    for nid in all_nodes:
        outs = outgoing_edges(nid)
        ps = [e["p"] for e in outs if e["p"] is not None]
        if ps:
            total = sum(ps)
            if abs(total - 1) > 0.01:
                st.warning(f"Outgoing probabilities from {node_label(nid)} sum to {total:.2f} (should be ~1).")

    render_graph()

# ---------------------
# TAB 2: Simulation
# ---------------------
with tabs[1]:
    st.header("Simulation Mode")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if all_nodes:
        if not st.session_state.sim["active"]:
            start_node = st.selectbox("Start Node", all_nodes, format_func=node_label, key="sim_start_node")
            if st.button("▶ Start Simulation"):
                start_sim(start_node)
        else:
            current = st.session_state.sim["current"]
            st.success(f"Current Node: {node_label(current)}")
            for nid in outgoing(current):
                if st.button(f"➡ {node_label(nid)}", key=f"sim_step_{nid}"):
                    step_sim(nid)
            if not outgoing(current):
                st.info("Reached a terminal node.")
            st.write("**Path so far:**", " → ".join(node_label(nid) for nid in st.session_state.sim["path"]))
            if st.button("Reset Simulation"):
                reset_sim()
            render_graph(st.session_state.highlight_edges)
    else:
        st.info("Add nodes to simulate.")

# ---------------------
# TAB 3: Monte Carlo
# ---------------------
with tabs[2]:
    st.header("Monte Carlo Simulation")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if all_nodes:
        start_node = st.selectbox("Start Node", all_nodes, format_func=node_label, key="mc_start_node")
        n_runs = st.number_input("Number of runs", 1, 100000, 1000, 100)
        max_steps = st.number_input("Max steps per run", 1, 1000, 50)
        if st.button("▶ Run Monte Carlo"):
            term, (highlight_edges, colors), path_counts = run_monte_carlo(start_node, int(n_runs), int(max_steps))
            st.dataframe(pd.DataFrame([{"Node": k, "Count": v, "Pct": v / n_runs} for k, v in term.items()]))
            st.dataframe(pd.DataFrame([{"Path": p, "Count": c, "Pct": c / n_runs} for p, c in path_counts.most_common(10)]))
            render_graph(highlight_edges, colors)
            excel_data = export_monte_carlo_to_excel(term, path_counts, int(n_runs))
            st.download_button("Download Monte Carlo Results (Excel)", data=excel_data, file_name="monte_carlo_results.xlsx")
    else:
        st.info("Add nodes to run Monte Carlo.")

# ---------------------
# TAB 4: Import / Export
# ---------------------
with tabs[3]:
    st.header("Import / Export")
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
            st.error("Invalid JSON.")
