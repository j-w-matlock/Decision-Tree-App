import json
import uuid
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – React Flow", layout="wide")
st.title("🌳 Decision Tree – Streamlit + React Flow (Embedded)")

# ---------------------------
# Session state
# ---------------------------
if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"

def node_kind_style(kind: str) -> dict:
    colors = {
        "event":    ("#1d4ed8", "#e0ecff"),
        "decision": ("#16a34a", "#e6f7eb"),
        "result":   ("#f97316", "#fff1e6"),
    }
    border, bg = colors.get(kind, ("#777", "#fff"))
    return {"border": f"2px solid {border}", "background": bg, "borderRadius": 6, "padding": 6, "minWidth": 120}

# ---------------------------
# Toolbar
# ---------------------------
st.subheader("Toolbar")

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

with c1:
    if st.button("＋ Event"):
        st.session_state.graph["nodes"].append({
            "id": new_node_id(),
            "type": "default",
            "position": {"x": 100 + 50 * len(st.session_state.graph["nodes"]), "y": 120},
            "data": {"label": "Event"},
            "style": node_kind_style("event"),
            "kind": "event"
        })
        st.rerun()

with c2:
    if st.button("＋ Decision"):
        st.session_state.graph["nodes"].append({
            "id": new_node_id(),
            "type": "default",
            "position": {"x": 100 + 50 * len(st.session_state.graph["nodes"]), "y": 220},
            "data": {"label": "Decision"},
            "style": node_kind_style("decision"),
            "kind": "decision"
        })
        st.rerun()

with c3:
    if st.button("＋ Result"):
        st.session_state.graph["nodes"].append({
            "id": new_node_id(),
            "type": "default",
            "position": {"x": 100 + 50 * len(st.session_state.graph["nodes"]), "y": 320},
            "data": {"label": "Result"},
            "style": node_kind_style("result"),
            "kind": "result"
        })
        st.rerun()

with c4:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(st.session_state.graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json"
    )

with c5:
    if st.button("🗑 Clear Canvas"):
        st.session_state.graph = {"nodes": [], "edges": []}
        st.rerun()

st.divider()

# ---------------------------
# Fallback test node
# ---------------------------
if not st.session_state.graph["nodes"]:
    st.session_state.graph["nodes"] = [{
        "id": "test",
        "type": "default",
        "position": {"x": 250, "y": 150},
        "data": {"label": "Hello React Flow"}
    }]

nodes = st.session_state.graph["nodes"]
edges = st.session_state.graph["edges"]
labels = {n["id"]: n["data"]["label"] for n in nodes}

# ---------------------------
# Edge Management
# ---------------------------
st.subheader("Manage Edges")

with st.form("add_edge_form", clear_on_submit=True):
    st.markdown("**Add Edge**")
    if nodes:
        src = st.selectbox("From (source node)", [n["id"] for n in nodes], format_func=lambda i: f"{labels[i]} ({i})")
        dst = st.selectbox("To (target node)", [n["id"] for n in nodes], format_func=lambda i: f"{labels[i]} ({i})")
        label = st.text_input("Label (optional)")
        prob = st.text_input("Probability (optional, e.g., 0.3)")
        submitted = st.form_submit_button("➕ Add Edge")
        if submitted:
            if src == dst:
