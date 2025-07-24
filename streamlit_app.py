import json
import uuid
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Decision Tree – PyVis", layout="wide")
st.title("🌳 Decision Tree – Interactive (Right-Click + Edges)")

# ---------------------------
# Session state
# ---------------------------
if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

if "selected_node" not in st.session_state:
    st.session_state.selected_node = None  # For edge creation

def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"

# ---------------------------
# PyVis builder
# ---------------------------
def build_pyvis_graph(graph):
    net = Network(height="600px", width="100%", directed=True, notebook=False)
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "size": 25,
        "font": {"size": 16, "face": "arial"},
        "shape": "box",
        "margin": 10
      },
      "edges": {
        "smooth": false,
        "arrows": {"to": {"enabled": true}},
        "font": {"size": 12, "align": "horizontal"}
      },
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 300}
      },
      "interaction": {
        "navigationButtons": true,
        "keyboard": true,
        "multiselect": true,
        "selectConnectedEdges": false
      }
    }
    """)
    # Add nodes
    for n in graph["nodes"]:
        color = {"event": "#e0ecff", "decision": "#e6f7eb", "result": "#fff1e6"}.get(n.get("kind", "event"), "#fff")
        border = {"event": "#1d4ed8", "decision": "#16a34a", "result": "#f97316"}.get(n.get("kind", "event"), "#777")
        net.add_node(n["id"], n["data"]["label"], color=color, borderWidth=2, borderWidthSelected=3)
    # Add edges
    for e in graph["edges"]:
        label = e.get("label") or ""
        prob = e.get("data", {}).get("prob")
        if prob is not None:
            if label:
                label = f"{label} (p={prob})"
            else:
                label = f"p={prob}"
        net.add_edge(e["source"], e["target"], label=label)
    return net

# ---------------------------
# Interactive Canvas
# ---------------------------
st.subheader("Canvas (Right-click to Add, Click→Right-click to Connect)")

net = build_pyvis_graph(st.session_state.graph)
html_file = "graph.html"
net.save_graph(html_file)

# Custom JS to add context menu and handle edge creation
custom_js = """
<script>
let selectedNode = null;

// Add custom right-click behavior
document.addEventListener("contextmenu", function(event) {
    event.preventDefault();
    var canvas = document.querySelector("canvas");
    if (!canvas || !canvas.getBoundingClientRect().contains(event.clientX, event.clientY)) return;

    var menu = document.createElement("div");
    menu.style.position = "fixed";
    menu.style.left = event.clientX + "px";
    menu.style.top = event.clientY + "px";
    menu.style.background = "#f8fafc";
    menu.style.border = "1px solid #ccc";
    menu.style.padding = "8px";
    menu.style.zIndex = 1000;

    const addEvent = document.createElement("div");
    addEvent.innerText = "Add Event Node";
    addEvent.onclick = function() {
        var label = prompt("Enter Event label:", "Event");
        if (label) {
            window.parent.postMessage({type: "add_node", kind: "event", label: label}, "*");
        }
        document.body.removeChild(menu);
    };
    menu.appendChild(addEvent);

    const addDecision = document.createElement("div");
    addDecision.innerText = "Add Decision Node";
    addDecision.onclick = function() {
        var label = prompt("Enter Decision label:", "Decision");
        if (label) {
            window.parent.postMessage({type: "add_node", kind: "decision", label: label}, "*");
        }
        document.body.removeChild(menu);
    };
    menu.appendChild(addDecision);

    const addResult = document.createElement("div");
    addResult.innerText = "Add Result Node";
    addResult.onclick = function() {
        var label = prompt("Enter Result label:", "Result");
        if (label) {
            window.parent.postMessage({type: "add_node", kind: "result", label: label}, "*");
        }
        document.body.removeChild(menu);
    };
    menu.appendChild(addResult);

    if (selectedNode) {
        const connectNode = document.createElement("div");
        connectNode.innerText = "Connect from " + selectedNode;
        connectNode.onclick = function() {
            var target = prompt("Enter target node ID:");
            if (target) {
                var label = prompt("Edge label (optional):", "");
                var prob = prompt("Probability (optional):", "");
                window.parent.postMessage({type: "add_edge", source: selectedNode, target: target, label: label, prob: prob}, "*");
            }
            document.body.removeChild(menu);
        };
        menu.appendChild(connectNode);
    }

    document.body.appendChild(menu);
    document.addEventListener("click", function() {
        if (menu) document.body.removeChild(menu);
    }, { once: true });
});

// Listen for node clicks (to prepare edge creation)
window.addEventListener("message", (event) => {
    if (event.data && event.data.type === "select_node") {
        selectedNode = event.data.nodeId;
    }
});
</script>
"""

with open(html_file, "r", encoding="utf-8") as f:
    html_data = f.read().replace("</body>", custom_js + "</body>")

components.html(html_data, height=650, scrolling=True)

# ---------------------------
# Communication with Streamlit
# ---------------------------
msg = st.experimental_get_query_params().get("msg", [""])[0]

if msg.startswith("add_node:"):
    parts = msg.split(":")
    kind = parts[1]
    label = ":".join(parts[2:])
    st.session_state.graph["nodes"].append({
        "id": new_node_id(),
        "data": {"label": label},
        "kind": kind
    })
    st.experimental_set_query_params()
    st.rerun()

if msg.startswith("add_edge:"):
    _, source, target, label, prob = msg.split(":", 4)
    p_val = float(prob) if prob else None
    st.session_state.graph["edges"].append({
        "id": new_edge_id(),
        "source": source,
        "target": target,
        "label": label if label else None,
        "data": {"prob": p_val} if p_val is not None else {}
    })
    st.experimental_set_query_params()
    st.rerun()

# ---------------------------
# Import/Export JSON
# ---------------------------
st.subheader("Import/Export")

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(st.session_state.graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json"
    )
with col2:
    uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
    if uploaded:
        st.session_state.graph = json.load(uploaded)
        st.success("Graph imported!")
        st.rerun()
