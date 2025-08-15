import json
import uuid

import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Mind Map Builder", layout="wide")
st.title("🧠 Mind Map Builder")


def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"


def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"


# ---------------------------
# Session state
# ---------------------------
if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

graph = st.session_state.graph


# ---------------------------
# Sidebar – Node Management
# ---------------------------
st.sidebar.header("🛠 Node Management")

with st.sidebar.expander("➕ Add Node", expanded=True):
    with st.form("add_node_form", clear_on_submit=True):
        node_label = st.text_input("Label")
        add_node_btn = st.form_submit_button("Add node")
    if add_node_btn and node_label:
        graph["nodes"].append(
            {"id": new_node_id(), "data": {"label": node_label}, "position": {"x": 0, "y": 0}}
        )
        st.rerun()

if graph["nodes"]:
    with st.sidebar.expander("✏️ Edit Node", expanded=True):
        node_options = {n["id"]: n["data"]["label"] for n in graph["nodes"]}
        node_id = st.selectbox("Node", list(node_options.keys()), format_func=lambda x: node_options[x])
        node = next(n for n in graph["nodes"] if n["id"] == node_id)
        with st.form(f"edit_node_form_{node_id}"):
            label = st.text_input("Label", value=node["data"]["label"])
            update_btn = st.form_submit_button("Update node")
        delete_btn = st.button("Delete node", key=f"del_node_{node_id}")
        if update_btn:
            node["data"]["label"] = label
            st.rerun()
        if delete_btn:
            graph["nodes"] = [n for n in graph["nodes"] if n["id"] != node_id]
            graph["edges"] = [e for e in graph["edges"] if e["source"] != node_id and e["target"] != node_id]
            st.rerun()


# ---------------------------
# Sidebar – Edge Management
# ---------------------------
st.sidebar.header("🔗 Edge Management")

if len(graph["nodes"]) >= 2:
    node_labels = {n["id"]: n["data"]["label"] for n in graph["nodes"]}

    with st.sidebar.expander("➕ Add Edge", expanded=True):
        with st.form("add_edge_form", clear_on_submit=True):
            source = st.selectbox("Source", list(node_labels.keys()), format_func=lambda x: node_labels[x])
            target = st.selectbox(
                "Target", [n["id"] for n in graph["nodes"] if n["id"] != source], format_func=lambda x: node_labels[x]
            )
            edge_label = st.text_input("Edge label (optional)")
            add_edge_btn = st.form_submit_button("Add edge")
            if add_edge_btn:
                if source == target:
                    st.warning("❌ Cannot connect a node to itself.")
                elif any(e for e in graph["edges"] if e["source"] == source and e["target"] == target):
                    st.warning("❌ Edge already exists.")
                else:
                    graph["edges"].append(
                        {"id": new_edge_id(), "source": source, "target": target, "label": edge_label or None}
                    )
                    st.rerun()

    if graph["edges"]:
        with st.sidebar.expander("✏️ Edit Edge", expanded=False):
            edge_options = {e["id"]: f"{node_labels[e['source']]} → {node_labels[e['target']]}" for e in graph["edges"]}
            edge_id = st.selectbox("Edge", list(edge_options.keys()), format_func=lambda x: edge_options[x])
            edge = next(e for e in graph["edges"] if e["id"] == edge_id)
            node_ids = list(node_labels.keys())
            with st.form(f"edit_edge_form_{edge_id}"):
                source_idx = node_ids.index(edge["source"]) if edge["source"] in node_ids else 0
                source = st.selectbox("Source", node_ids, index=source_idx, format_func=lambda x: node_labels[x])
                target_opts = [nid for nid in node_ids if nid != source]
                target_idx = target_opts.index(edge["target"]) if edge["target"] in target_opts else 0
                target = st.selectbox("Target", target_opts, index=target_idx, format_func=lambda x: node_labels[x])
                edge_label = st.text_input("Edge label (optional)", value=edge.get("label") or "")
                update_btn = st.form_submit_button("Update edge")
            delete_btn = st.button("Delete edge", key=f"del_edge_{edge_id}")
            if update_btn:
                if source == target:
                    st.warning("❌ Cannot connect a node to itself.")
                elif any(
                    e for e in graph["edges"] if e["source"] == source and e["target"] == target and e["id"] != edge_id
                ):
                    st.warning("❌ Edge already exists.")
                else:
                    edge.update({"source": source, "target": target, "label": edge_label or None})
                    st.rerun()
            if delete_btn:
                graph["edges"] = [e for e in graph["edges"] if e["id"] != edge_id]
                st.rerun()


# ---------------------------
# Global Actions (Top Controls)
# ---------------------------
st.markdown("### Actions")
action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(graph, indent=2),
        file_name="mind_map.json",
        mime="application/json",
        use_container_width=True,
    )

with action_col2:
    uploaded = st.file_uploader("Upload JSON", type=["json"])
    if uploaded:
        st.session_state.graph = json.load(uploaded)
        st.rerun()

with action_col3:
    if st.button("🗑 Clear Canvas", use_container_width=True):
        st.session_state.graph = {"nodes": [], "edges": []}
        st.rerun()


 # ---------------------------
 # Canvas Visualization
 # ---------------------------
st.markdown("### Canvas")

# Build Fabric.js objects for nodes and edges
objects = []
for node in graph["nodes"]:
    objects.append(
        {
            "type": "textbox",
            "text": node["data"]["label"],
            "left": node["position"].get("x", 0),
            "top": node["position"].get("y", 0),
            "width": 150,
            "height": 50,
            "fontSize": 16,
            "backgroundColor": "#ffffff",
            "strokeWidth": 1,
            "stroke": "#000000",
            "editable": False,
            "name": node["id"],
        }
    )

for edge in graph["edges"]:
    src = next(n for n in graph["nodes"] if n["id"] == edge["source"])
    tgt = next(n for n in graph["nodes"] if n["id"] == edge["target"])
    x1 = src["position"].get("x", 0) + 75
    y1 = src["position"].get("y", 0) + 25
    x2 = tgt["position"].get("x", 0) + 75
    y2 = tgt["position"].get("y", 0) + 25
    objects.append(
        {
            "type": "line",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "stroke": "#000000",
            "strokeWidth": 1,
            "selectable": False,
            "evented": False,
            "name": edge["id"],
        }
    )
    if edge.get("label"):
        objects.append(
            {
                "type": "textbox",
                "text": edge["label"],
                "left": (x1 + x2) / 2,
                "top": (y1 + y2) / 2,
                "fontSize": 12,
                "backgroundColor": "#ffffff",
                "editable": False,
                "selectable": False,
                "evented": False,
                "name": f"label_{edge['id']}",
            }
        )

canvas_result = st_canvas(
    initial_drawing={"objects": objects},
    height=600,
    width=1000,
    drawing_mode="transform",
    background_color="#f0f0f0",
    update_streamlit=True,
    key="mindmap_canvas",
)

# Update node positions from canvas
if canvas_result.json_data:
    for obj in canvas_result.json_data.get("objects", []):
        if obj.get("type") == "textbox" and obj.get("name") in {n["id"] for n in graph["nodes"]}:
            node = next(n for n in graph["nodes"] if n["id"] == obj["name"])
            node["position"] = {"x": obj.get("left", 0), "y": obj.get("top", 0)}


