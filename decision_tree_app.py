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
            new_type = st.selectbox("New type", ["event", "response", "outcome"], index=["event","response","outcome"].index(node["type"]), key=f"edit_type_{s_
