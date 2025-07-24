import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – React Flow", layout="wide")
st.title("🌳 Decision Tree – Streamlit + React Flow (Embedded)")

# Initialize session state
if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

# ---- Toolbar ----
st.subheader("Toolbar")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("+ Event"):
        st.session_state.graph["nodes"].append({
            "id": f"n{len(st.session_state.graph['nodes']) + 1}",
            "type": "default",
            "position": {"x": 100, "y": 100},
            "data": {"label": "Event"}
        })
with col2:
    if st.button("+ Decision"):
        st.session_state.graph["nodes"].append({
            "id": f"n{len(st.session_state.graph['nodes']) + 1}",
            "type": "default",
            "position": {"x": 200, "y": 100},
            "data": {"label": "Decision"}
        })
with col3:
    if st.button("+ Result"):
        st.session_state.graph["nodes"].append({
            "id": f"n{len(st.session_state.graph['nodes']) + 1}",
            "type": "default",
            "position": {"x": 300, "y": 100},
            "data": {"label": "Result"}
        })
with col4:
    st.download_button(
        label="💾 Export JSON",
        data=json.dumps(st.session_state.graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json"
    )

# ---- React Flow HTML ----
st.subheader("Canvas")
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
      const nodes = {json.dumps(st.session_state.graph["nodes"])};
      const edges = {json.dumps(st.session_state.graph["edges"])};

      ReactDOM.render(
        React.createElement(ReactFlowProvider, null,
          React.createElement("div", {{ style: {{ width: "100%", height: "500px" }} }},
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
components.html(reactflow_html, height=500, scrolling=False)

# ---- Import JSON ----
st.subheader("Import JSON")
uploaded = st.file_uploader("Upload JSON", type=["json"])
if uploaded:
    st.session_state.graph = json.load(uploaded)
    st.success("Graph imported!")
