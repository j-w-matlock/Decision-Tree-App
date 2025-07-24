import json
import uuid
from typing import Dict, List

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
            "edges": []    # [{"from": id, "to": id}]
        }
    if "sim" not in st.session_state:
        st.session_state.sim = {
            "active": False,
            "current": None,
            "path": []   # list of node ids
        }

_init_state()


# -------------
# Core helpers
# -------------
def new_node_id() -> str:
    # uuid avoids collisions after deletions
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
    n = st.session_state.tree["nodes"][node_id]
    n["label"] = new_label.strip() if new_label else "(unnamed)"
    n["type"] = new_type


def delete_node(node_id: str):
    # Remove node
    st.session_state.tree["nodes"].pop(node_id, None)
    # Remove edges referencing this node
    st.session_state.tree["edges"] = [
        e for e in st.session_state.tree["edges"] if e["from"] != node_id and e["to"] != node_id
    ]
    # If simulation is using this node, reset it
    if st.session_state.sim["current"] == node_id or node_id in st.session_state.sim["path"]:
        reset_sim()


def add_edge(src: str, dst: str):
    if src == dst:
        st.warning("Can't create self-loop edge (from == to).")
        return
    # Avoid duplicates
    if any(e["from"] == src and e["to"] == dst for e in st.session_state.tree["edges"]):
        st.info("Edge already exists.")
        return
    st.session_state.tree["edges"].append({"from": src, "to": dst})


def delete_edge(index: int):
    if 0 <= index < len(st.session_state.tree["edges"]):
        st.session_state.tree["edges"].pop(index)


def outgoing(node_id: str) -> List[str]:
    return [e["to"] for e in st.session_state.tree["edges"] if e["from"] == node_id]


def node_label(node_id: str) -> str:
    n = st.session_state.tree["nodes"][node_id]
    return f"{n['label']} ({n['type']})"


def reset_sim():
    st.session_state.sim["active"] = False
    st.session_state.sim["current"] = None
    st.session_state.sim["path"] = []


def start_sim(start_node: str):
    st.session_state.sim["active"] = True
    st.session_state.sim["current"] = start_node
    st.session_state.sim["path"] = [start_node]


def step_sim(next_node: str):
    st.session_state.sim["current"] = next_node
    st.session_state.sim["path"].append(next_node)


def is_terminal(node_id: str) -> bool:
    return len(outgoing(node_id)) == 0


# ---------------
# Visualization
# ---------------
def render_graph():
    dot = Digraph()
    for node_id, node in st.session_state.tree["nodes"].items():
        color = {
            "event": "lightblue",
            "response": "lightgreen",
            "outcome": "orange"
        }.get(node["type"], "white")
        dot.node(node_id, f"{node['label']} ({node['type']})", style="filled", fillcolor=color)

    for edge in st.session_state.tree["edges"]:
        dot.edge(edge["from"], edge["to"])

    st.graphviz_chart(dot, use_container_width=True)


# ------------
# UI Sections
# ------------
st.title("🌳 Decision Tree Builder (Streamlit)")

tabs = st.tabs(["Build", "Simulate", "Import / Export", "Debug"])

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
            selected_edit = st.selectbox("Select node to edit", all_nodes, format_func=node_label)
            node = st.session_state.tree["nodes"][selected_edit]
            new_label = st.text_input("New label", value=node["label"], key=f"edit_label_{selected_edit}")
            new_type = st.selectbox("New type", ["event", "response", "outcome"], index=["event","response","outcome"].index(node["type"]), key=f"edit_type_{selected_edit}")
            if st.button("💾 Save changes", key=f"save_{selected_edit}"):
                edit_node(selected_edit, new_label, new_type)
                st.success("Node updated.")
        else:
            st.info("No nodes yet.")

        st.divider()
        st.header("Delete Node")
        if all_nodes:
            selected_delete = st.selectbox("Select node to delete", all_nodes, format_func=node_label, key="delete_node_select")
            confirm = st.checkbox("I understand this will remove attached edges too.", key="confirm_delete")
            if st.button("🗑️ Delete Node", disabled=not confirm):
                delete_node(selected_delete)
                st.success("Node deleted.")
        else:
            st.info("No nodes to delete.")

        st.divider()
        st.header("Add Edge")
        all_nodes = list(st.session_state.tree["nodes"].keys())
        if all_nodes:
            from_node = st.selectbox("From", all_nodes, format_func=node_label, key="edge_from")
            to_node = st.selectbox("To", all_nodes, format_func=node_label, key="edge_to")
            if st.button("➕ Add Edge"):
                add_edge(from_node, to_node)
        else:
            st.info("Create nodes first.")

        st.divider()
        st.header("Delete Edge")
        edges = st.session_state.tree["edges"]
        if edges:
            # Build a friendly label list for selection
            labels = [
                f"{i}: {node_label(e['from'])}  →  {node_label(e['to'])}"
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
        render_graph()

# -----------------------
# TAB 2: Simulation Mode
# -----------------------
with tabs[1]:
    st.header("Simulation")
    if len(st.session_state.tree["nodes"]) == 0:
        st.info("Create some nodes first.")
    else:
        sim_col1, sim_col2 = st.columns([1, 2])

        with sim_col1:
            if not st.session_state.sim["active"]:
                # Start simulation
                start_candidates = list(st.session_state.tree["nodes"].keys())
                start_node = st.selectbox("Pick a start node", start_candidates, format_func=node_label)
                if st.button("▶️ Start simulation"):
                    start_sim(start_node)
            else:
                st.success(f"Simulation running. Current node: {node_label(st.session_state.sim['current'])}")
                if st.button("⏹️ Reset simulation"):
                    reset_sim()

        with sim_col2:
            if st.session_state.sim["active"]:
                current = st.session_state.sim["current"]
                st.subheader(f"Current: {node_label(current)}")

                outs = outgoing(current)
                if outs:
                    st.markdown("**Choose next:**")
                    for nid in outs:
                        if st.button(f"➡️ {node_label(nid)}", key=f"step_{nid}"):
                            step_sim(nid)
                else:
                    st.info("Reached a terminal node (no outgoing edges).")
                    if st.button("🔁 Restart"):
                        reset_sim()

                # Show the traversed path
                st.markdown("### Path so far")
                path_labels = [node_label(nid) for nid in st.session_state.sim["path"]]
                st.write(" → ".join(path_labels))

    st.divider()
    st.subheader("Tree (for reference)")
    render_graph()

# -------------------------
# TAB 3: Import / Export
# -------------------------
with tabs[2]:
    st.header("💾 Export / Import")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Export")
        exported = json.dumps(st.session_state.tree, indent=2)
        st.download_button(
            "Download tree.json",
            data=exported,
            file_name="decision_tree.json",
            mime="application/json"
        )

    with col_b:
        st.subheader("Import")
        uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
        if uploaded is not None:
            try:
                raw = json.load(uploaded)
                # Basic validation
                if "nodes" in raw and "edges" in raw:
                    st.session_state.tree = raw
                    reset_sim()
                    st.success("Tree imported successfully!")
                else:
                    st.error("Invalid format. JSON must contain 'nodes' and 'edges'.")
            except Exception as e:
                st.error(f"Failed to import: {e}")

    st.divider()
    st.subheader("Preview JSON")
    st.code(exported, language="json")

# --------------
# TAB 4: Debug
# --------------
with tabs[3]:
    st.header("Debug")
    st.write("**Session state snapshot:**")
    st.json({
        "tree": st.session_state.tree,
        "sim": st.session_state.sim
    })
