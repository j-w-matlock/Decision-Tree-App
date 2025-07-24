import json
import pandas as pd
import streamlit as st
from collections import Counter
import random
from typing import Dict, List, Tuple

# ---- Import our component
from st_react_flow import react_flow

st.set_page_config(page_title="Decision Tree (React Flow in Streamlit)", layout="wide")

st.title("🌳 Decision Tree – Streamlit + React Flow")

# ------------------------------------------------------------------------------------
# Helpers for MC simulation on the Python side (edges can have optional 'prob' values)
# ------------------------------------------------------------------------------------
def run_monte_carlo(graph: Dict, start_node_id: str, n_runs: int, max_steps: int = 50):
    nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
    outgoing = {}
    for e in graph.get("edges", []):
        outgoing.setdefault(e["source"], []).append(e)

    terminal_outcomes = Counter()
    path_counts = Counter()

    for _ in range(n_runs):
        cur = start_node_id
        path = [cur]
        for __ in range(max_steps):
            edges = outgoing.get(cur, [])
            if not edges:  # terminal
                break
            probs = [e.get("data", {}).get("prob", 1.0) or 1.0 for e in edges]
            total = sum(probs)
            if total <= 0:
                probs = [1.0] * len(edges)
                total = float(len(edges))
            probs = [p / total for p in probs]
            nxt_edge = random.choices(edges, weights=probs, k=1)[0]
            cur = nxt_edge["target"]
            path.append(cur)
        terminal_outcomes[cur] += 1
        path_counts[" → ".join(path)] += 1

    return terminal_outcomes, path_counts

# ---------------------------
# Default (empty) graph JSON
# ---------------------------
DEFAULT_GRAPH = {
    "nodes": [],
    "edges": []
}

# Keep the graph in session_state
if "graph" not in st.session_state:
    st.session_state.graph = DEFAULT_GRAPH

st.sidebar.header("Actions")
dev = st.sidebar.checkbox("Development mode (React dev server @ http://localhost:5173)", value=False)

# Send graph → React, get new graph back
graph = react_flow("react_flow_canvas", value=st.session_state.graph, dev=dev)

# Merge back
if graph is not None:
    st.session_state.graph = graph

left, right = st.columns([1, 1])

with left:
    st.subheader("▶ Monte Carlo (Python-side)")
    if st.session_state.graph["nodes"]:
        node_ids = [n["id"] for n in st.session_state.graph["nodes"]]
        labels = {n["id"]: n["data"]["label"] for n in st.session_state.graph["nodes"]}
        start_id = st.selectbox("Start node", node_ids, format_func=lambda x: labels.get(x, x))
        runs = st.number_input("Number of runs", 1, 100000, 1000, 100)
        if st.button("Run Monte Carlo"):
            term, paths = run_monte_carlo(st.session_state.graph, start_id, int(runs))
            st.write("Terminal node frequencies")
            term_df = pd.DataFrame(
                [{"node_id": k, "count": v, "pct": v / int(runs)} for k, v in term.items()]
            ).sort_values("count", ascending=False)
            st.dataframe(term_df, use_container_width=True)

            st.write("Top paths")
            path_df = pd.DataFrame(
                [{"path": p, "count": c, "pct": c / int(runs)} for p, c in paths.most_common(20)]
            )
            st.dataframe(path_df, use_container_width=True)

            # Excel download
            from io import BytesIO
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                term_df.to_excel(writer, index=False, sheet_name="terminal")
                path_df.to_excel(writer, index=False, sheet_name="paths")
            st.download_button("Download Monte Carlo results (xlsx)", buf.getvalue(), "mc_results.xlsx")

with right:
    st.subheader("📦 Import / Export")
    st.download_button(
        "Download JSON",
        data=json.dumps(st.session_state.graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json",
    )
    uploaded = st.file_uploader("Upload JSON", type=["json"])
    if uploaded:
        st.session_state.graph = json.load(uploaded)
        st.success("Imported.")
