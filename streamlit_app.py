import json
import uuid
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – Connected Layout", layout="wide")
st.title("🌳 Decision Tree – Connected (Event → Decision → Result)")

# ---------------------------
# Helpers & state
# ---------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"

if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

graph = st.session_state.graph

# Sync updates from query params if needed
if "graph" in st.query_params:
    try:
        g = json.loads(urllib.parse.unquote(st.query_params["graph"]))
        if isinstance(g, dict) and "nodes" in g and "edges" in g:
            st.session_state.graph = g
            graph = g
    except Exception as e:
        st.error(f"Failed to parse incoming graph: {e}")
    finally:
        st.query_params = {}

# ---------------------------
# Sidebar Node Editor
# ---------------------------
st.sidebar.header("🛠 Node Management")

# Add new node
with st.sidebar.expander("Add Node"):
    new_label = st.text_input("Label", key="new_label")
    node_type = st.selectbox("Type", ["event", "decision", "result"], key="new_type")
    if st.button("➕ Add Node"):
        if new_label.strip():
            new_id = new_node_id()
            graph["nodes"].append({
                "id": new_id,
                "data": {"label": new_label},
                "kind": node_type
            })
            st.success(f"Node '{new_label}' added.")
            st.rerun()
        else:
            st.warning("Please enter a label.")

# Editable Node Table
if graph["nodes"]:
    st.sidebar.subheader("Edit Nodes")
    node_changes = []
    for i, node in enumerate(graph["nodes"]):
        with st.sidebar.expander(f"Node: {node['data']['label']}"):
            new_label = st.text_input(f"Label for {node['id']}", node["data"]["label"], key=f"node_label_{i}")
            new_kind = st.selectbox(f"Type for {node['id']}", ["event", "decision", "result"],
                                    index=["event", "decision", "result"].index(node.get("kind", "event")),
                                    key=f"node_type_{i}")
            if new_label != node["data"]["label"] or new_kind != node.get("kind", "event"):
                node_changes.append((i, new_label, new_kind))
            if st.button(f"🗑 Delete {node['data']['label']}", key=f"delete_node_{i}"):
                node_id = node["id"]
                graph["nodes"] = [n for n in graph["nodes"] if n["id"] != node_id]
                graph["edges"] = [e for e in graph["edges"] if e["source"] != node_id and e["target"] != node_id]
                st.success(f"Deleted node {node['data']['label']}.")
                st.rerun()
    if node_changes:
        for i, new_label, new_kind in node_changes:
            graph["nodes"][i]["data"]["label"] = new_label
            graph["nodes"][i]["kind"] = new_kind
        st.rerun()

# ---------------------------
# Sidebar Edge Editor
# ---------------------------
st.sidebar.header("🔗 Edge Management")

# Add Edge
if len(graph["nodes"]) >= 2:
    with st.sidebar.expander("Add Edge"):
        node_labels = {n["id"]: n["data"]["label"] for n in graph["nodes"]}
        source = st.selectbox("Source", list(node_labels.keys()), format_func=lambda x: node_labels[x], key="edge_src")
        target = st.selectbox("Target",
                              [n["id"] for n in graph["nodes"] if n["id"] != source],
                              format_func=lambda x: node_labels[x], key="edge_tgt")
        edge_label = st.text_input("Edge Label (optional)", key="edge_label")
        edge_prob = st.number_input("Probability (optional)", min_value=0.0, max_value=1.0, step=0.01, key="edge_prob")
        if st.button("➕ Add Edge"):
            new_edge = {
                "id": new_edge_id(),
                "source": source,
                "target": target,
                "label": edge_label or None,
                "data": {"prob": edge_prob} if edge_prob else {}
            }
            graph["edges"].append(new_edge)
            st.success(f"Connected '{node_labels[source]}' → '{node_labels[target]}'.")
            st.rerun()

# Editable Edge Table
if graph["edges"]:
    st.sidebar.subheader("Edit Edges")
    edge_changes = []
    for i, edge in enumerate(graph["edges"]):
        with st.sidebar.expander(f"Edge {edge['source']} → {edge['target']}"):
            new_label = st.text_input(f"Label for {edge['id']}", edge.get("label", "") or "", key=f"edge_label_{i}")
            new_prob = st.number_input(f"Probability for {edge['id']}",
                                       value=edge.get("data", {}).get("prob", 0.0),
                                       min_value=0.0, max_value=1.0, step=0.01,
                                       key=f"edge_prob_{i}")
            if new_label != edge.get("label") or new_prob != edge.get("data", {}).get("prob", 0.0):
                edge_changes.append((i, new_label, new_prob))
            if st.button(f"🗑 Delete Edge {edge['id']}", key=f"delete_edge_{i}"):
                graph["edges"] = [e for e in graph["edges"] if e["id"] != edge["id"]]
                st.success(f"Deleted edge {edge['id']}.")
                st.rerun()
    if edge_changes:
        for i, new_label, new_prob in edge_changes:
            graph["edges"][i]["label"] = new_label or None
            graph["edges"][i]["data"]["prob"] = new_prob
        st.rerun()

# ---------------------------
# Canvas Export/Import
# ---------------------------
c1, c2, c3 = st.columns(3)
with c1:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json",
        use_container_width=True,
    )

with c2:
    uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
    if uploaded:
        try:
            st.session_state.graph = json.load(uploaded)
            st.success("Graph imported.")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

with c3:
    if st.button("🗑 Clear Canvas", use_container_width=True):
        st.session_state.graph = {"nodes": [], "edges": []}
        st.rerun()

with st.expander("Current graph JSON (debug)"):
    st.code(json.dumps(graph, indent=2))

# ---------------------------
# Canvas Visualization (vis-network)
# ---------------------------
nodes_js = json.dumps([
    {
        "id": n["id"],
        "label": n["data"]["label"],
        "shape": "box",
        "color": {
            "background": {
                "event": "#e0ecff",
                "decision": "#e6f7eb",
                "result": "#fff1e6",
            }.get(n.get("kind", "event"), "#fff"),
            "border": {
                "event": "#1d4ed8",
                "decision": "#16a34a",
                "result": "#f97316",
            }.get(n.get("kind", "event"), "#777"),
        },
        "borderWidth": 2,
        "margin": 10,
    }
    for n in graph["nodes"]
])

edges_js = json.dumps([
    {
        "id": e["id"],
        "from": e["source"],
        "to": e["target"],
        "label": (
            f"{e.get('label') or ''}"
            f"{' (p='+str(e.get('data', {}).get('prob'))+')' if e.get('data', {}).get('prob') is not None else ''}"
        ).strip()
    }
    for e in graph["edges"]
])

html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    html, body {{ height: 100%; margin: 0; background: #f8fafc; }}
    #network {{
      height: 600px;
      background: #f1f5f9;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
    }}
  </style>
</head>
<body>
  <div id="network"></div>
  <script>
    const nodes = new vis.DataSet({nodes_js});
    const edges = new vis.DataSet({edges_js});
    const container = document.getElementById('network');
    const data = {{ nodes, edges }};
    const options = {{
      layout: {{
        hierarchical: {{
          enabled: true,
          direction: "UD",
          sortMethod: "directed",
          nodeSpacing: 150,
          treeSpacing: 200,
          levelSeparation: 200
        }}
      }},
      edges: {{
        arrows: {{ to: {{ enabled: true }} }},
        smooth: true
      }},
      physics: false,
      interaction: {{ dragView: true, zoomView: true }}
    }};
    const network = new vis.Network(container, data, options);
  </script>
</body>
</html>
"""
components.html(html, height=650, scrolling=False)
