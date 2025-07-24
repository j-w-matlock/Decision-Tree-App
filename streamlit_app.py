import json
import uuid
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – React Flow", layout="wide")
st.title("🌳 Decision Tree – Streamlit + React Flow (Embedded)")

# ---------------------------
# Session state bootstrapping
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
# UI: Nodes
# ---------------------------
st.subheader("Toolbar")

c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])

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
# UI: Edges (Create/Delete)
# ---------------------------
st.subheader("Edges")

nodes = st.session_state.graph["nodes"]
edges = st.session_state.graph["edges"]
node_ids = [n["id"] for n in nodes]
labels = {n["id"]: n["data"]["label"] for n in nodes}

with st.form("add_edge_form", clear_on_submit=True):
    st.markdown("**Add Edge**")
    if node_ids:
        src = st.selectbox("From (source)", node_ids, format_func=lambda i: f"{labels[i]} ({i})")
        dst = st.selectbox("To (target)", node_ids, format_func=lambda i: f"{labels[i]} ({i})")
        label = st.text_input("Label (optional)")
        prob = st.text_input("Probability (optional, e.g. 0.3)")
        submitted = st.form_submit_button("➕ Add edge")
        if submitted:
            if src == dst:
                st.warning("Source and target must be different.")
            else:
                try:
                    p_val = None if prob.strip() == "" else float(prob)
                except Exception:
                    p_val = None
                edges.append({
                    "id": new_edge_id(),
                    "source": src,
                    "target": dst,
                    "label": label if label else None,
                    "data": {"prob": p_val} if p_val is not None else {}
                })
                st.success("Edge added.")
                st.rerun()
    else:
        st.info("Add some nodes first to create edges.")

if edges:
    st.markdown("**Existing edges**")
    edge_descriptions = [
        f"{e['id']}: {labels.get(e['source'], e['source'])} → {labels.get(e['target'], e['target'])}"
        + (f" | label='{e.get('label')}'" if e.get('label') else "")
        + (f" | p={e.get('data', {}).get('prob')}" if e.get('data', {}).get('prob') is not None else "")
        for e in edges
    ]
    idx_to_delete = st.selectbox("Delete edge", list(range(len(edges))), format_func=lambda i: edge_descriptions[i])
    if st.button("🗑 Delete selected edge"):
        edges.pop(idx_to_delete)
        st.success("Edge deleted.")
        st.rerun()
else:
    st.info("No edges yet.")

st.divider()

# ---------------------------
# Canvas
# ---------------------------
st.subheader("Canvas")

# ReactFlow UMD needs nodes/edges with certain keys.
# We'll pass our nodes/edges directly; ReactFlow will show labels from node.data.label
# and edge.label, probabilities won't be rendered, but are carried in data.
reactflow_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>React Flow</title>
    <style>
      html, body, #root {{
        height: 100%;
        margin: 0;
        background: #f0f0f0;
      }}
      .react-flow__node {{
        border: 1px solid #777;
        padding: 5px;
        border-radius: 3px;
        background: white;
      }}
    </style>
    <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/reactflow/dist/umd/react-flow.production.min.js"></script>
  </head>
  <body>
    <div id="root"></div>
    <script>
      const {{ ReactFlow, ReactFlowProvider, MiniMap, Controls, Background }} = window.ReactFlow;

      const nodes = {json.dumps(nodes)};
      const edges = {json.dumps(edges)};

      ReactDOM.render(
        React.createElement(ReactFlowProvider, null,
          React.createElement("div", {{ style: {{ width: "100%", height: "600px" }} }},
            React.createElement(ReactFlow, {{
              nodes: nodes,
              edges: edges,
              fitView: true
            }},
              React.createElement(MiniMap, null),
              React.createElement(Controls, null),
              React.createElement(Background, null)
            )
          )
        ),
        document.getElementById("root")
      );
    </script>
  </body>
</html>
"""
components.html(reactflow_html, height=620, scrolling=False)

# ---------------------------
# Import JSON
# ---------------------------
st.subheader("Import JSON")
uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
if uploaded:
    try:
        st.session_state.graph = json.load(uploaded)
        st.success("Graph imported!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to import: {e}")
