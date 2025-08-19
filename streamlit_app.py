import json
import uuid

import streamlit as st
from st_react_flow import react_flow
from streamlit_agraph import agraph, Node, Edge, Config


# Supported node shapes for the ``streamlit_agraph`` renderer
NODE_SHAPES = [
    "dot",
    "square",
    "triangle",
    "triangleDown",
    "star",
    "hexagon",
    "diamond",
]

st.set_page_config(page_title="Mind Map Builder", layout="wide")
# Title and basic config
st.title("🧠 Mind Map Builder")

# ---------------------------
# Canvas settings
# ---------------------------
st.sidebar.header("⚙️ Canvas Settings")
canvas_renderer = st.sidebar.radio(
    "Renderer", ["React Flow", "Agraph"], index=0, help="Choose the graph canvas implementation"
)

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
        node_shape = st.selectbox("Shape", NODE_SHAPES, index=0)
        add_node_btn = st.form_submit_button("Add node")
    if add_node_btn and node_label:
        node_index = len(graph["nodes"])
        offset = 50
        position = {"x": node_index * offset, "y": node_index * offset}
        graph["nodes"].append(
            {
                "id": new_node_id(),
                "data": {"label": node_label, "shape": node_shape},
                "position": position,
            }
        )
        st.session_state.graph = graph

if graph["nodes"]:
    with st.sidebar.expander("✏️ Edit Node", expanded=True):
        node_options = {n["id"]: n["data"]["label"] for n in graph["nodes"]}
        node_id = st.selectbox("Node", list(node_options.keys()), format_func=lambda x: node_options[x])
        node = next(n for n in graph["nodes"] if n["id"] == node_id)
        with st.form(f"edit_node_form_{node_id}"):
            label = st.text_input("Label", value=node["data"]["label"])
            shape_val = node["data"].get("shape", "dot")
            shape_index = NODE_SHAPES.index(shape_val) if shape_val in NODE_SHAPES else 0
            shape = st.selectbox("Shape", NODE_SHAPES, index=shape_index)
            update_btn = st.form_submit_button("Update node")
        delete_btn = st.button("Delete node", key=f"del_node_{node_id}")
        if update_btn:
            node["data"]["label"] = label
            node["data"]["shape"] = shape
        if delete_btn:
            graph["nodes"] = [n for n in graph["nodes"] if n["id"] != node_id]
            graph["edges"] = [e for e in graph["edges"] if e["source"] != node_id and e["target"] != node_id]


# ---------------------------
# Sidebar – Edge Management
# ---------------------------
st.sidebar.header("🔗 Edge Management")

if len(graph["nodes"]) >= 2:
    node_labels = {n["id"]: n["data"]["label"] for n in graph["nodes"]}

    with st.sidebar.expander("➕ Add Edge", expanded=True):
        with st.form("add_edge_form"):
            source = st.selectbox(
                "Source", list(node_labels.keys()), format_func=lambda x: node_labels[x], key="add_edge_source"
            )
            target = st.selectbox(
                "Target",
                [n["id"] for n in graph["nodes"] if n["id"] != source],
                format_func=lambda x: node_labels[x],
                key="add_edge_target",
            )
            edge_label = st.text_input("Edge label (optional)")
            edge_color = st.color_picker("Color", "#000000")
            add_edge_btn = st.form_submit_button("Add edge")
            if add_edge_btn:
                if source == target:
                    st.warning("❌ Cannot connect a node to itself.")
                elif any(e for e in graph["edges"] if e["source"] == source and e["target"] == target):
                    st.warning("❌ Edge already exists.")
                else:
                    graph["edges"].append(
                        {
                            "id": new_edge_id(),
                            "source": source,
                            "target": target,
                            "label": edge_label or None,
                            "color": edge_color,
                        }
                    )

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
                edge_color = st.color_picker("Color", value=edge.get("color", "#000000"))
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
                    edge.update({
                        "source": source,
                        "target": target,
                        "label": edge_label or None,
                        "color": edge_color,
                    })
            if delete_btn:
                graph["edges"] = [e for e in graph["edges"] if e["id"] != edge_id]


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

with action_col3:
    if st.button("🗑 Clear Canvas", use_container_width=True):
        st.session_state.graph = {"nodes": [], "edges": []}


 # ---------------------------
 # Canvas Visualization
 # ---------------------------
st.markdown("### Canvas")

if canvas_renderer == "React Flow":
    result = react_flow(key="mindmap", value=graph)
    if result:
        graph["nodes"] = result.get("nodes", [])
        graph["edges"] = result.get("edges", [])
else:
    agraph_nodes = [
        Node(
            id=n["id"],
            label=n["data"]["label"],
            shape=n["data"].get("shape", "dot"),
            x=n.get("position", {}).get("x"),
            y=n.get("position", {}).get("y"),
        )
        for n in graph["nodes"]
    ]
    agraph_edges = [
        Edge(source=e["source"], target=e["target"], label=e.get("label"), color=e.get("color"))
        for e in graph["edges"]
    ]
    config = Config(
        width=750,
        height=500,
        directed=True,
        physics=False,
        stabilization=False,
    )
    agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)


