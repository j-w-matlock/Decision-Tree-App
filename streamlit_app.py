import json
import streamlit as st
from streamlit_elements import elements, dashboard, mui, reactflow

st.set_page_config(page_title="Decision Tree – React Flow", layout="wide")
st.title("🌳 Decision Tree – Streamlit + React Flow (Elements)")

# Session state for storing nodes/edges
if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

# Toolbar
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
    if st.button("💾 Export JSON"):
        st.download_button(
            label="Download",
            data=json.dumps(st.session_state.graph, indent=2),
            file_name="decision_tree.json",
            mime="application/json"
        )

# React Flow Canvas
st.subheader("Canvas")
with elements("react_flow"):
    reactflow_component = reactflow.ReactFlow(
        elements=st.session_state.graph["nodes"] + st.session_state.graph["edges"],
        style={"width": "100%", "height": 500}
    )
    reactflow_component.Controls()

# Import JSON
st.subheader("Import JSON")
uploaded = st.file_uploader("Upload JSON", type=["json"])
if uploaded:
    st.session_state.graph = json.load(uploaded)
    st.success("Graph imported!")
