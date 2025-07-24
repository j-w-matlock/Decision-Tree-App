import json
import uuid
import random
from typing import List, Dict, Tuple
from collections import Counter

import pandas as pd
import streamlit as st
from graphviz import Digraph

st.set_page_config(page_title="Decision Tree Builder", layout="wide")

# -----------------------
# Session state bootstrap
# -----------------------
def _init_state():
    if "tree" not in st.session_state:
        st.session_state.tree = {
            "nodes": {},   # {node_id: {"id": str, "label": str, "type": "event"|"response"|"outcome"}}
            "edges": []    # [{"from": id, "to": id, "p": Optional[float]}]
        }
    if "sim" not in st.session_state:
        st.session_state.sim = {"active": False, "current": None, "path": []}

def reset_tree():
    st.session_state.tree = {"nodes": {}, "edges": []}
    reset_sim()

def reset_sim():
    st.session_state.sim = {"active": False, "current": None, "path": []}

_init_state()

# -------------
# Core helpers
# -------------
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
        e for e in st.session_state.tree["edges"] if e["from"] != node_id and e["to"] != node_id
    ]
    if (st.session_state.sim["current"] == node_id or
            node_id in st.session_state.sim["path"]):
        reset_sim()

def add_edge(src: str, dst: str, p: float | None = None):
    if src == dst:
        st.warning("Can't create self-loop edge.")
        return
    if src not in st.session_state.tree["nodes"] or dst not in st.session_state.tree["nodes"]:
        st.warning("Invalid nodes for edge.")
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
    st.session_state.sim["active"] = True
    st.session_state.sim["current"] = start_node
    st.session_state.sim["path"] = [start_node]

def step_sim(next_node: str):
    st.session_state.sim["current"] = next_node
    st.session_state.sim["path"].append(next_node)

def is_terminal(node_id: str) -> bool:
    return len(outgoing(node_id)) == 0

def sanitize_prob(x) -> float | None:
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if v < 0:
            return None
        return v
    except:
        return None

# ---------------
# Visualization
# ---------------
def render_graph():
    dot = Digraph()
    for node_id, node in st.session_state.tree["nodes"].items():
        color = {"event": "lightblue", "response": "lightgreen", "outcome": "orange"}.get(node["type"], "white")
        safe_label = node['label'].replace('"', '\\"')
        dot.node(node_id, f"{safe_label} ({node['type']})", style="filled", fillcolor=color)

    for edge in st.session_state.tree["edges"]:
        if edge["from"] in st.session_state.tree["nodes"] and edge["to"] in st.session_state.tree["nodes"]:
            label = ""
            if edge.get("p") is not None:
                label = f"p={edge['p']:.3f}"
            dot.edge(edge["from"], edge["to"], label=label)

    st.graphviz_chart(dot, use_container_width=True)

# -----------------------
# Monte Carlo logic
# -----------------------
def choose_next_with_probs(current: str) -> str | None:
    outs = outgoing_edges(current)
    if not outs:
        return None

    # Check if at least one edge has p set
    probs = [e.get("p") for e in outs]
    if all(p is None for p in probs):
        # uniform
        return random.choice([e["to"] for e in outs])

    # Use provided (non-None) probs, treat None as 0, then normalize
    cleaned = [0.0 if p is None else max(p, 0.0) for p in probs]
    total = sum(cleaned)
    if total <= 0.0:
        # fallback to uniform if probs invalid
        return random.choice([e["to"] for e in outs])

    normalized = [p / total for p in cleaned]
    r = random.random()
    cum = 0.0
    for e, p in zip(outs, normalized):
        cum += p
        if r <= cum:
            return e["to"]
    # numerical edge case
    return outs[-1]["to"]

def run_monte_carlo(start_node: str, n_runs: int, max_steps: int) -> Tuple[Counter, Counter]:
    """Returns (terminal_outcomes_counter, full_path_counter)"""
    terminal_outcomes = Counter()
    paths = Counter()

    for _ in range(n_runs):
        current = start_node
        path = [current]
        for _step in range(max_steps):
            nxt = choose_next_with_probs(current)
            if nxt is None:
                break
            current = nxt
            path.append(current)
            if is_terminal(current):
                break
        # record
        label = node_label(current)
        terminal_outcomes[label] += 1
        path_str = " → ".join(node_label(n) for n in path)
        paths[path_str] += 1

    return terminal_outcomes, paths


# ------------
# UI Sections
# ------------
st.title("🌳 Decision Tree Builder (Streamlit) — with Optional Probabilities & Monte Carlo")

# Reset Tree Button
if st.button("🔄 Reset Entire Tree"):
    reset_tree()
    st.success("Tree reset.")

tabs = st.tabs(["Build", "Simulate", "Monte Carlo", "Import / Export", "Debug"])

# ---------------------
# TAB 1: Build the tree
# ---------------------
with tabs[0]:
    left, right = st.columns([1, 2])

    with left:
        st.header("Add Node")
        with st.form("add_node_form", clear_on_submit=True):
            node_label_in = st.text_input("Label")
            node_type_in = st.selectbox("Type", ["event", "response", "outcome"])
            submitted = st.form_submit_button("➕ Add Node")
            if submitted:
                node_id = add_node(node_label_in, node_type_in)
                st.success(f"Node added: {node_id}")

        st.divider()
        st.header("Edit Node")
        all_nodes = list(st.session_state.tree["nodes"].keys())
        if all_nodes:
            selected_edit = st.selectbox("Select node", all_nodes, format_func=node_label, key="edit_node")
            node = st.session_state.tree["nodes"][selected_edit]
            new_label = st.text_input("New label", value=node["label"], key=f"edit_label_{selected_edit}")
            new_type = st.selectbox(
                "New type",
                ["event", "response", "outcome"],
                index=["event", "response", "outcome"].index(node["type"]),
                key=f"edit_type_{selected_edit}"
            )
            if st.button("💾 Save changes", key=f"save_{selected_edit}"):
                edit_node(selected_edit, new_label, new_type)
                st.success("Node updated.")
        else:
            st.info("No nodes yet.")

        st.divider()
        st.header("Delete Node")
        if all_nodes:
            selected_delete = st.selectbox("Select node", all_nodes, format_func=node_label, key="delete_node")
            confirm = st.checkbox("I understand this will remove attached edges too.", key="confirm_delete")
            if st.button("🗑️ Delete Node", disabled=not confirm):
                delete_node(selected_delete)
                st.success("Node deleted.")
        else:
            st.info("No nodes to delete.")

        st.divider()
        st.header("Add Edge")
        if all_nodes:
            from_node = st.selectbox("From", all_nodes, format_func=node_label, key="edge_from")
            to_node = st.selectbox("To", all_nodes, format_func=node_label, key="edge_to")
            edge_p = st.text_input("Optional probability (0–1, blank = none)", key="edge_prob")
            if st.button("➕ Add Edge"):
                p = sanitize_prob(edge_p)
                add_edge(from_node, to_node, p)
        else:
            st.info("Create nodes first.")

        st.divider()
        st.header("Edit Edge Probabilities")
        edges = st.session_state.tree["edges"]
        if edges:
            for i, e in enumerate(edges):
                with st.expander(f"Edge {i}: {node_label(e['from'])} → {node_label(e['to'])}"):
                    cur = "" if e.get("p") is None else str(e["p"])
                    newp = st.text_input("Probability (blank = none)", value=cur, key=f"edge_edit_{i}")
                    if st.button("Save", key=f"edge_save_{i}"):
                        st.session_state.tree["edges"][i]["p"] = sanitize_prob(newp)
                        st.success("Saved.")
        else:
            st.info("No edges to edit.")

        st.divider()
        st.header("Delete Edge")
        if edges:
            labels = [
                f"{i}: {node_label(e['from'])} → {node_label(e['to'])}" + (f" (p={e['p']})" if e.get("p") is not None else "")
                for i, e in enumerate(edges)
            ]
            idx_to_del = st.selectbox("Select edge", list(range(len(edges))), format_func=lambda i: labels[i])
            if st.button("🗑️ Delete Edge"):
                delete_edge(idx_to_del)
                st.success("Edge deleted.")
        else:
            st.info("No edges to delete.")

    with right:
        st.subheader("Current Tree Visualization")
        # Quick probability sanity: warn if any node has outgoing probs that don't sum ~1
        for nid in st.session_state.tree["nodes"]:
            outs = outgoing_edges(nid)
            ps = [e.get("p") for e in outs if e.get("p") is not None]
            if ps:
                s = sum(ps)
                if abs(s - 1.0) > 1e-6:
                    st.warning(f"Outgoing probabilities from {node_label(nid)} sum to {s:.4f} (will be renormalized in Monte Carlo).")
        render_graph()

# -----------------------
# TAB 2: Simulation Mode
# -----------------------
with tabs[1]:
    st.header("Simulation (manual path selection)")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if not all_nodes:
        st.info("Create some nodes first.")
    else:
        # defensive
        if (st.session_state.sim["current"] not in st.session_state.tree["nodes"] and
                st.session_state.sim["current"] is not None):
            reset_sim()

        sim_col1, sim_col2 = st.columns([1, 2])
        with sim_col1:
            if not st.session_state.sim["active"]:
                start_node = st.selectbox("Pick a start node", all_nodes, format_func=node_label, key="sim_start_node")
                if st.button("▶️ Start simulation"):
                    start_sim(start_node)
            else:
                st.success(f"Simulation running: {node_label(st.session_state.sim['current'])}")
                if st.button("⏹️ Reset simulation"):
                    reset_sim()

        with sim_col2:
            if st.session_state.sim["active"]:
                current = st.session_state.sim["current"]
                st.subheader(f"Current: {node_label(current)}")
                outs = outgoing(current)
                if outs:
                    st.markdown("**Choose next step:**")
                    for nid in outs:
                        if st.button(f"➡️ {node_label(nid)}", key=f"step_{nid}"):
                            step_sim(nid)
                else:
                    st.info("Reached a terminal node.")
                    if st.button("🔁 Restart"):
                        reset_sim()
                st.markdown("### Path so far")
                st.write(" → ".join(node_label(nid) for nid in st.session_state.sim["path"]))

    st.divider()
    st.subheader("Tree (for reference)")
    render_graph()

# -----------------------
# TAB 3: Monte Carlo
# -----------------------
with tabs[2]:
    st.header("Monte Carlo Simulation (uses probabilities if provided, else uniform)")
    all_nodes = list(st.session_state.tree["nodes"].keys())
    if not all_nodes:
        st.info("Create some nodes first.")
    else:
        mc_col1, mc_col2 = st.columns([1, 1])
        with mc_col1:
            start_node = st.selectbox("Start node", all_nodes, format_func=node_label, key="mc_start")
            n_runs = st.number_input("Number of runs", min_value=1, value=1000, step=100)
            max_steps = st.number_input("Max steps per run", min_value=1, value=50, step=1)
            if st.button("▶️ Run Monte Carlo"):
                term, paths = run_monte_carlo(start_node, int(n_runs), int(max_steps))

                st.subheader("Terminal node frequencies")
                term_df = pd.DataFrame(
                    [{"terminal": k, "count": v, "pct": v / n_runs} for k, v in term.items()]
                ).sort_values("count", ascending=False)
                st.dataframe(term_df, use_container_width=True)

                st.subheader("Most common full paths")
                top_paths = paths.most_common(20)
                path_df = pd.DataFrame(
                    [{"path": p, "count": c, "pct": c / n_runs} for p, c in top_paths]
                )
                st.dataframe(path_df, use_container_width=True)

        with mc_col2:
            st.subheader("Tree (for reference)")
            # probs sanity check
            for nid in st.session_state.tree["nodes"]:
                outs = outgoing_edges(nid)
                ps = [e.get("p") for e in outs if e.get("p") is not None]
                if ps:
                    s = sum(ps)
                    if abs(s - 1.0) > 1e-6:
                        st.info(f"Outgoing probabilities from {node_label(nid)} sum to {s:.4f} (renormalized).")
            render_graph()

# -------------------------
# TAB 4: Import / Export
# -------------------------
with tabs[3]:
    st.header("💾 Export / Import")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Export")
        exported = json.dumps(st.session_state.tree, indent=2)
        st.download_button("Download tree.json", data=exported, file_name="decision_tree.json", mime="application/json")

    with col_b:
        st.subheader("Import")
        uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
        if uploaded is not None:
            try:
                raw = json.load(uploaded)
                if "nodes" in raw and "edges" in raw:
                    valid_ids = set(raw["nodes"].keys())
                    cleaned_edges = []
                    for e in raw["edges"]:
                        if e.get("from") in valid_ids and e.get("to") in valid_ids:
                            ee = {"from": e["from"], "to": e["to"], "p": sanitize_prob(e.get("p"))}
                            cleaned_edges.append(ee)
                    raw["edges"] = cleaned_edges
                    st.session_state.tree = raw
                    reset_sim()
                    st.success("Tree imported successfully!")
                else:
                    st.error("Invalid JSON format.")
            except Exception as e:
                st.error(f"Failed to import: {e}")

    st.divider()
    st.subheader("Preview JSON")
    st.code(exported, language="json")


with tabs[4]:
    st.header("Debug Info")
    st.json({"tree": st.session_state.tree, "sim": st.session_state.sim})
