import json
import uuid
import urllib.parse
from collections import defaultdict

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – Auto-Compute & Export", layout="wide")
st.title("🌳 Decision Tree – Left → Right with Auto-Compute & PNG Export")

# ---------------------------
# Helpers
# ---------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"

def validate_graph(graph: dict) -> list[str]:
    warnings = []
    nodes_map = {n["id"]: n for n in graph["nodes"]}
    outgoing_probs = defaultdict(float)
    for e in graph["edges"]:
        if e.get("data", {}).get("prob") is not None:
            outgoing_probs[e["source"]] += e["data"]["prob"]

    for n in graph["nodes"]:
        if n.get("kind") == "decision":
            total = outgoing_probs.get(n["id"], 0.0)
            if any(e.get("data", {}).get("prob") is not None for e in graph["edges"] if e["source"] == n["id"]):
                if not (0.99 <= total <= 1.01):
                    warnings.append(f"Decision node “{n['data']['label']}” outgoing probabilities sum to {total:.3f} (should be 1.0).")

    for e in graph["edges"]:
        s = nodes_map[e["source"]]
        t = nodes_map[e["target"]]
        if s.get("kind") == "event" and t.get("kind") == "event":
            warnings.append(f"Edge {s['data']['label']} → {t['data']['label']} is Event→Event (disallowed).")
        if e["source"] == e["target"]:
            warnings.append(f"Self-loop detected on “{s['data']['label']}”.")
    return warnings

def auto_compute_probabilities(graph: dict):
    """Assign equal probability to outgoing edges of decision nodes if none or zero is set."""
    decision_nodes = [n for n in graph["nodes"] if n.get("kind") == "decision"]
    for dn in decision_nodes:
        outgoing = [e for e in graph["edges"] if e["source"] == dn["id"]]
        if outgoing:
            if all(e.get("data", {}).get("prob") in [None, 0] for e in outgoing):
                p = 1.0 / len(outgoing)
                for e in outgoing:
                    e["data"]["prob"] = round(p, 3)

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
        new_label = st.text_input("Label", placeholder="e.g. User signs up", help="Enter a descriptive name for the node.")
        node_type = st.selectbox("Type", ["event", "decision", "result"], help="Select the type of node.")
        submitted = st.form_submit_button("Add node", help="Add this new node to the decision tree.")
        if submitted and new_label.strip():
            graph["nodes"].append({"id": new_node_id(), "data": {"label": new_label}, "kind": node_type})
            st.rerun()

# ---------------------------
# Sidebar – Edge Management
# ---------------------------
st.sidebar.header("🔗 Edge Management")

if len(graph["nodes"]) >= 2:
    with st.sidebar.expander("➕ Add Edge", expanded=True):
        node_labels = {n["id"]: n["data"]["label"] for n in graph["nodes"]}
        with st.form("add_edge_form", clear_on_submit=True):
            source = st.selectbox("Source", list(node_labels.keys()), format_func=lambda x: node_labels[x],
                                  help="Select the starting node.")
            target = st.selectbox("Target", [n["id"] for n in graph["nodes"] if n["id"] != source],
                                  format_func=lambda x: node_labels[x],
                                  help="Select the ending node.")
            edge_label = st.text_input("Edge label (optional)", help="Add an optional label, e.g., 'Yes' or 'No'.")
            edge_prob_enabled = st.checkbox("Add probability", help="Assign a probability to this edge.")
            edge_prob = None
            if edge_prob_enabled:
                edge_prob = st.number_input("Probability", min_value=0.0, max_value=1.0, step=0.01, value=0.5,
                                            help="Set probability between 0 and 1.")
            add_edge_btn = st.form_submit_button("Add edge", help="Create a connection between the selected nodes.")
            if add_edge_btn:
                src_kind = next((n.get("kind", "event") for n in graph["nodes"] if n["id"] == source), "event")
                tgt_kind = next((n.get("kind", "event") for n in graph["nodes"] if n["id"] == target), "event")
                if source == target:
                    st.warning("❌ Cannot connect a node to itself.")
                elif src_kind == "event" and tgt_kind == "event":
                    st.warning("❌ Cannot connect Event → Event directly.")
                elif any(e for e in graph["edges"] if e["source"] == source and e["target"] == target):
                    st.warning("❌ Edge already exists.")
                else:
                    graph["edges"].append({
                        "id": new_edge_id(),
                        "source": source,
                        "target": target,
                        "label": edge_label or None,
                        "data": {"prob": edge_prob} if edge_prob_enabled else {}
                    })
                    st.rerun()

# ---------------------------
# Global Actions (Top Controls)
# ---------------------------
st.markdown("### Actions")
action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json",
        help="Download the current decision tree as a JSON file.",
        use_container_width=True
    )

with action_col2:
    uploaded = st.file_uploader(
        "Upload JSON",
        type=["json"],
        help="Upload a previously saved decision tree JSON."
    )
    if uploaded:
        st.session_state.graph = json.load(uploaded)
        st.rerun()

with action_col3:
    if st.button(
        "🗑 Clear Canvas",
        use_container_width=True,
        help="Remove all nodes and edges from the canvas."
    ):
        st.session_state.graph = {"nodes": [], "edges": []}
        st.rerun()

with action_col4:
    if st.button(
        "⚙ Auto-Compute",
        use_container_width=True,
        help="Evenly distribute probabilities across outgoing edges of decision nodes (if none are set)."
    ):
        auto_compute_probabilities(graph)
        st.success("Probabilities auto-computed.")
        st.rerun()

# ---------------------------
# Validation Warnings
# ---------------------------
warnings = validate_graph(graph)
if warnings:
    st.markdown("#### ⚠️ Warnings")
    for w in warnings:
        st.warning(w)

# ---------------------------
# Canvas Visualization
# ---------------------------
nodes_js = json.dumps([
    {
        "id": n["id"],
        "label": n["data"]["label"],
        "shape": "box",
        "color": {
            "background": {"event": "#e0ecff", "decision": "#e6f7eb", "result": "#fff1e6"}.get(n.get("kind", "event"), "#fff"),
            "border": {"event": "#1d4ed8", "decision": "#16a34a", "result": "#f97316"}.get(n.get("kind", "event"), "#777"),
        },
        "borderWidth": 2, "margin": 10,
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

vis_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <style>
    html, body {{ height: 100%; margin: 0; background: #f8fafc; }}
    #network {{
      height: 620px;
      background: #f1f5f9;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      position: relative;
    }}
    #exportBtn {{
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 999;
      padding: 6px 12px;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }}
    #exportBtn:hover {{
      background: #1e40af;
    }}
  </style>
</head>
<body>
  <button id="exportBtn" title="Click to save the current canvas as a PNG image.">Export PNG</button>
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
          direction: "LR",
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

    // Export PNG
    document.getElementById("exportBtn").addEventListener("click", () => {{
      html2canvas(container).then(canvas => {{
        const link = document.createElement('a');
        link.download = 'decision_tree.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      }});
    }});
  </script>
</body>
</html>
"""
st.markdown("### Canvas")
components.html(vis_html, height=650, scrolling=False)
