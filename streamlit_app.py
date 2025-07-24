# decision_tree_app.py
import streamlit as st
import json
from graphviz import Digraph

st.set_page_config(page_title="Decision Tree Builder", layout="wide")

# Initialize tree in session_state
if "tree" not in st.session_state:
    st.session_state["tree"] = {"nodes": [], "edges": []}

def add_node(label, node_type):
    node_id = f"n{len(st.session_state['tree']['nodes'])+1}"
    st.session_state['tree']["nodes"].append({
        "id": node_id,
        "label": label,
        "type": node_type
    })
    return node_id

def add_edge(from_node, to_node):
    st.session_state['tree']["edges"].append({"from": from_node, "to": to_node})

st.title("🌳 Decision Tree Builder")

# Sidebar: Add Nodes
with st.sidebar:
    st.header("Add Node")
    node_label = st.text_input("Node Label")
    node_type = st.selectbox("Node Type", ["event", "response", "outcome"])
    if st.button("➕ Add Node"):
        new_node_id = add_node(node_label, node_type)
        st.success(f"Node added: {new_node_id} - {node_label}")

    st.header("Add Edge")
    if st.session_state["tree"]["nodes"]:
        node_ids = [n["id"] for n in st.session_state["tree"]["nodes"]]
        from_node = st.selectbox("From", node_ids, key="from_edge")
        to_node = st.selectbox("To", node_ids, key="to_edge")
        if st.button("➕ Add Edge"):
            add_edge(from_node, to_node)
            st.success(f"Edge added: {from_node} → {to_node}")

    st.header("Export/Import")
    if st.button("💾 Export Tree"):
        st.download_button(
            label="Download Tree JSON",
            data=json.dumps(st.session_state['tree'], indent=2),
            file_name="decision_tree.json",
            mime="application/json"
        )

# Main Content: Display Tree
st.subheader("Current Tree Visualization")
dot = Digraph()
for node in st.session_state["tree"]["nodes"]:
    color = "lightblue" if node["type"] == "event" else "lightgreen" if node["type"] == "response" else "orange"
    dot.node(node["id"], f"{node['label']} ({node['type']})", style="filled", fillcolor=color)

for edge in st.session_state["tree"]["edges"]:
    dot.edge(edge["from"], edge["to"])

st.graphviz_chart(dot)
