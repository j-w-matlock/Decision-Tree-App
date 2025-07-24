import json
import uuid
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – vis-network", layout="wide")
st.title("🌳 Decision Tree – ComfyUI-style (Right‑Click Interactive)")

# ---------------------------
# Helpers & state
# ---------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

# Ingest updates coming back from the front-end via query params
if "graph" in st.query_params:
    try:
        g = json.loads(urllib.parse.unquote(st.query_params["graph"]))
        if isinstance(g, dict) and "nodes" in g and "edges" in g:
            st.session_state.graph = g
    except Exception as e:
        st.error(f"Failed to parse incoming graph: {e}")
    finally:
        # clear to avoid re-importing on any refresh
        st.query_params = {}

graph = st.session_state.graph

# ---------------------------
# UI: Import / Export / Clear
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
    st.code(json.dumps(st.session_state.graph, indent=2))

# ---------------------------
# Prepare data for the front-end
# ---------------------------
# vis-network needs: nodes: [{id, label, ...}], edges: [{id, from, to, label, ...}]
nodes_js = json.dumps([
    {
        "id": n["id"],
        "label": n["data"]["label"],
        "kind": n.get("kind", "event"),
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

# Keep metadata so we can rebuild the server-side JSON accurately
node_meta = {
    n["id"]: {"kind": n.get("kind", "event"), "label": n["data"]["label"]}
    for n in graph["nodes"]
}
edge_meta = {
    e["id"]: {
        "label": e.get("label"),
        "prob": e.get("data", {}).get("prob")
    }
    for e in graph["edges"]
}
meta_js = json.dumps({"nodes": node_meta, "edges": edge_meta})

# ---------------------------
# Robust vis-network HTML + JS (right-click working)
# ---------------------------
html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    html, body {{
      height: 100%;
      margin: 0;
      background: #f8fafc;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, sans-serif;
    }}
    #wrapper {{
      position: relative;
      height: 620px;
    }}
    #network {{
      position: absolute;
      inset: 0;
      background: #f1f5f9;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
    }}
    .context-menu {{
      position: fixed;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      z-index: 999999;
      padding: 4px 0;
      min-width: 200px;
    }}
    .context-menu button {{
      display: block;
      width: 100%;
      padding: 6px 12px;
      background: transparent;
      border: none;
      text-align: left;
      cursor: pointer;
      font-size: 14px;
    }}
    .context-menu button:hover {{
      background: #f1f5f9;
    }}
    .floating-sync {{
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 999998;
      border: none;
      background: #1d4ed8;
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      font-size: 14px;
    }}
    .floating-sync:hover {{
      background: #2563eb;
    }}
    #selected-label {{
      position: absolute;
      top: 50px;
      right: 10px;
      background: #fff8dc;
      border: 1px solid #cbd5e1;
      padding: 4px 8px;
      border-radius: 4px;
      display: none;
      font-size: 12px;
      z-index: 999998;
    }}
  </style>
</head>
<body>
  <div id="wrapper">
    <div id="network"></div>
    <button class="floating-sync" id="syncButton" title="Send changes to Streamlit">Sync to Streamlit</button>
    <div id="selected-label">Selected node: <span id="selected-node-id"></span></div>
  </div>

  <script>
    // ---------- initial data from Streamlit ----------
    const nodeMeta = {meta_js};       // {{ nodes: {{id: {{kind, label}}}}, edges: {{id: {{label, prob}}}} }}
    const nodeMetaNodes = nodeMeta.nodes || (nodeMeta.nodes = {{}});
    const nodeMetaEdges = nodeMeta.edges || (nodeMeta.edges = {{}});
    const initialNodes = {nodes_js};
    const initialEdges = {edges_js};

    // ---------- vis-network setup ----------
    const container = document.getElementById('network');
    const nodes = new vis.DataSet(initialNodes);
    const edges = new vis.DataSet(initialEdges);

    const data = {{ nodes, edges }};
    const options = {{
      interaction: {{
        multiselect: true,
        selectConnectedEdges: false,
        dragView: true,
        zoomView: true
      }},
      physics: {{
        stabilization: {{ iterations: 300 }}
      }},
      edges: {{
        arrows: {{
          to: {{ enabled: true }}
        }}
      }},
      nodes: {{
        shape: 'box',
        margin: 10,
        borderWidth: 2,
        chosen: {{
          node: (values, id, selected) => {{
            values.borderWidth = selected ? 4 : 2;
          }}
        }}
      }}
    }};

    const network = new vis.Network(container, data, options);

    // Disable default browser context menu on container
    container.addEventListener("contextmenu", e => e.preventDefault());

    let selectedNode = null;
    const selectedLabelDiv = document.getElementById('selected-label');
    const selectedNodeSpan = document.getElementById('selected-node-id');

    function updateSelectedLabel() {{
      if (selectedNode) {{
        selectedNodeSpan.textContent = selectedNode;
        selectedLabelDiv.style.display = 'block';
      }} else {{
        selectedLabelDiv.style.display = 'none';
      }}
    }}

    // Left click selects a node
    network.on("click", params => {{
      if (params.nodes && params.nodes.length > 0) {{
        selectedNode = params.nodes[0];
      }} else {{
        selectedNode = null;
      }}
      updateSelectedLabel();
    }});

    // Our robust right-click handler on the network container
    network.body.container.addEventListener('contextmenu', function(e) {{
      e.preventDefault();
      const pointer = network.getPointer(e);
      // network.getNodeAt expects DOM coords: use pointer.DOM.x/y if available
      const domPoint = (pointer && pointer.DOM) ? pointer.DOM : {{ x: e.offsetX, y: e.offsetY }};
      const nodeAt = network.getNodeAt({{ x: domPoint.x, y: domPoint.y }});
      showContextMenu(e.clientX, e.clientY, nodeAt);
    }});

    function hideContextMenu() {{
      const menu = document.querySelector('.context-menu');
      if (menu) menu.remove();
    }}

    function showContextMenu(x, y, nodeIdOrNull) {{
      hideContextMenu();

      const entries = [];
      if (!nodeIdOrNull) {{
        // right-click on empty space
        entries.push({{ label: 'Add Event Node', action: () => addNode('event') }});
        entries.push({{ label: 'Add Decision Node', action: () => addNode('decision') }});
        entries.push({{ label: 'Add Result Node', action: () => addNode('result') }});
      }} else {{
        // right-click on a node
        entries.push({{
          label: 'Select this node',
          action: () => {{
            selectedNode = nodeIdOrNull;
            updateSelectedLabel();
          }}
        }});
        if (selectedNode && selectedNode !== nodeIdOrNull) {{
          entries.push({{
            label: 'Connect selected → this node',
            action: () => {{
              connectNodes(selectedNode, nodeIdOrNull);
              selectedNode = null;
              updateSelectedLabel();
            }}
          }});
        }}
        entries.push({{
          label: 'Edit label',
          action: () => {{
            editNodeLabel(nodeIdOrNull);
          }}
        }});
        entries.push({{
          label: 'Delete node',
          action: () => deleteNode(nodeIdOrNull)
        }});
      }}

      const menu = document.createElement('div');
      menu.className = 'context-menu';
      menu.style.left = x + 'px';
      menu.style.top = y + 'px';

      entries.forEach(entry => {{
        const btn = document.createElement('button');
        btn.textContent = entry.label;
        btn.onclick = () => {{
          entry.action();
          hideContextMenu();
        }};
        menu.appendChild(btn);
      }});

      document.body.appendChild(menu);
      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    function colorFor(kind) {{
      if (kind === 'decision') return {{
        background: '#e6f7eb', border: '#16a34a'
      }};
      if (kind === 'result') return {{
        background: '#fff1e6', border: '#f97316'
      }};
      return {{ background: '#e0ecff', border: '#1d4ed8' }}; // event default
    }}

    function addNode(kind) {{
      const id = 'n_' + Math.random().toString(36).substring(2, 8);
      const label = prompt('Enter ' + kind + ' label:', kind.charAt(0).toUpperCase() + kind.slice(1));
      if (!label) return;

      const colors = colorFor(kind);
      nodeMetaNodes[id] = {{ kind, label }};

      nodes.add({{
        id,
        label,
        shape: 'box',
        color: {{
          background: colors.background,
          border: colors.border
        }},
        borderWidth: 2,
        margin: 10
      }});

      // Optionally place it near center
      const viewPos = network.getViewPosition();
      const scale = network.getScale();
      const x = viewPos.x;
      const y = viewPos.y;
      // small async to ensure node exists
      requestAnimationFrame(() => {{
        network.moveNode(id, x + (Math.random() * 100 - 50)/scale, y + (Math.random() * 100 - 50)/scale);
      }});
    }}

    function editNodeLabel(nodeId) {{
      const current = nodes.get(nodeId);
      const newLabel = prompt('New label', current.label || '');
      if (newLabel === null) return;
      nodes.update({{ id: nodeId, label: newLabel }});
      if (!nodeMetaNodes[nodeId]) nodeMetaNodes[nodeId] = {{ kind: 'event', label: '' }};
      nodeMetaNodes[nodeId].label = newLabel;
    }}

    function deleteNode(nodeId) {{
      // Remove edges attached to node
      const toRemove = edges.get().filter(e => e.from === nodeId || e.to === nodeId).map(e => e.id);
      edges.remove(toRemove);
      if (nodeMetaEdges) {{
        toRemove.forEach(id => delete nodeMetaEdges[id]);
      }}
      nodes.remove(nodeId);
      delete nodeMetaNodes[nodeId];
      if (selectedNode === nodeId) {{
        selectedNode = null;
        updateSelectedLabel();
      }}
    }}

    function connectNodes(sourceId, targetId) {{
      const label = prompt('Edge label (optional):', '');
      const probStr = prompt('Probability (optional):', '');
      const id = 'e_' + Math.random().toString(36).substring(2, 8);
      const text = (label || '') + (probStr ? (label ? ' ' : '') + '(p=' + probStr + ')' : '');
      edges.add({{ id, from: sourceId, to: targetId, label: text }});
      nodeMetaEdges[id] = {{
        label: label || null,
        prob: probStr ? parseFloat(probStr) : null
      }};
    }}

    // Send back to Streamlit
    document.getElementById('syncButton').onclick = function() {{
      const rebuilt = {{
        nodes: nodes.get().map(n => {{
          const meta = nodeMetaNodes[n.id] || {{ kind: 'event', label: n.label }};
          return {{
            id: n.id,
            type: 'default',
            position: {{}}, // we aren't storing vis coords
            data: {{ label: meta.label }},
            kind: meta.kind
          }};
        }}),
        edges: edges.get().map(e => {{
          const meta = nodeMetaEdges[e.id] || {{ label: null, prob: null }};
          return {{
            id: e.id,
            source: e.from,
            target: e.to,
            label: meta.label,
            data: meta.prob != null ? {{ prob: meta.prob }} : {{}}
          }};
        }})
      }};
      const payload = encodeURIComponent(JSON.stringify(rebuilt));
      const base = window.location.href.split('?')[0];
      window.location.href = base + '?graph=' + payload;
    }};
  </script>
</body>
</html>
"""

components.html(html, height=650, scrolling=False)
