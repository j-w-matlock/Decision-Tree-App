import json
import uuid
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – vis-network", layout="wide")
st.title("🌳 Decision Tree – ComfyUI-style (Double-Click Menu)")

# ---------------------------
# Helpers & state
# ---------------------------
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
# Robust vis-network HTML + JS (Double-Click Menu)
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
    const nodeMeta = {meta_js};
    const nodes = new vis.DataSet({nodes_js});
    const edges = new vis.DataSet({edges_js});

    const container = document.getElementById('network');
    const data = {{ nodes: nodes, edges: edges }};
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
        arrows: {{ to: {{ enabled: true }} }}
      }},
      nodes: {{
        shape: 'box',
        margin: 10,
        borderWidth: 2
      }}
    }};
    const network = new vis.Network(container, data, options);

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

    // Context Menu Helpers
    function hideContextMenu() {{
      const menu = document.querySelector('.context-menu');
      if (menu) menu.remove();
    }}

    function showContextMenu(x, y, entries) {{
      hideContextMenu();
      const menu = document.createElement('div');
      menu.className = 'context-menu';
      menu.style.left = x + 'px';
      menu.style.top = y + 'px';
      entries.forEach(entry => {{
        const btn = document.createElement('button');
        btn.textContent = entry.label;
        btn.onclick = () => {{ entry.action(); hideContextMenu(); }};
        menu.appendChild(btn);
      }});
      document.body.appendChild(menu);
      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    // Double-click event
    network.on('doubleClick', function(params) {{
      const x = params.event.srcEvent.clientX;
      const y = params.event.srcEvent.clientY;
      if (params.nodes.length === 0) {{
        showContextMenu(x, y, [
          {{ label: 'Add Event Node', action: () => addNode('event') }},
          {{ label: 'Add Decision Node', action: () => addNode('decision') }},
          {{ label: 'Add Result Node', action: () => addNode('result') }},
        ]);
      }} else {{
        const nodeId = params.nodes[0];
        showContextMenu(x, y, [
          {{ label: 'Select this node', action: () => {{ selectedNode = nodeId; updateSelectedLabel(); }} }},
          ...(selectedNode && selectedNode !== nodeId ? [
            {{ label: 'Connect selected → this node', action: () => {{
              connectNodes(selectedNode, nodeId);
              selectedNode = null;
              updateSelectedLabel();
            }}}}
          ] : []),
          {{ label: 'Edit label', action: () => editNodeLabel(nodeId) }},
          {{ label: 'Delete node', action: () => deleteNode(nodeId) }}
        ]);
      }}
    }});

    function addNode(kind) {{
      const id = 'n_' + Math.random().toString(36).substring(2, 8);
      const label = prompt('Enter ' + kind + ' label:', kind.charAt(0).toUpperCase() + kind.slice(1));
      if (!label) return;
      const color = kind === 'event' ? '#e0ecff' : kind === 'decision' ? '#e6f7eb' : '#fff1e6';
      const border = kind === 'event' ? '#1d4ed8' : kind === 'decision' ? '#16a34a' : '#f97316';
      nodes.add({{
        id, label,
        shape: 'box',
        color: {{ background: color, border: border }},
        borderWidth: 2,
        margin: 10
      }});
      nodeMeta.nodes[id] = {{ kind, label }};
    }}

    function editNodeLabel(nodeId) {{
      const node = nodes.get(nodeId);
      const newLabel = prompt('New label:', node.label || '');
      if (newLabel !== null) {{
        nodes.update({{ id: nodeId, label: newLabel }});
        nodeMeta.nodes[nodeId].label = newLabel;
      }}
    }}

    function deleteNode(nodeId) {{
      nodes.remove(nodeId);
      edges.remove(edges.get().filter(e => e.from === nodeId || e.to === nodeId).map(e => e.id));
      delete nodeMeta.nodes[nodeId];
    }}

    function connectNodes(sourceId, targetId) {{
      const label = prompt('Edge label (optional):', '');
      const probStr = prompt('Probability (optional):', '');
      const id = 'e_' + Math.random().toString(36).substring(2, 8);
      edges.add({{
        id, from: sourceId, to: targetId,
        label: (label || '') + (probStr ? ' (p=' + probStr + ')' : '')
      }});
      nodeMeta.edges[id] = {{ label: label || null, prob: probStr ? parseFloat(probStr) : null }};
    }}

    // Sync button
    document.getElementById('syncButton').onclick = function() {{
      const rebuilt = {{
        nodes: nodes.get().map(n => {{
          return {{
            id: n.id,
            type: 'default',
            position: {{}},
            data: {{ label: nodeMeta.nodes?.[n.id]?.label ?? n.label }},
            kind: nodeMeta.nodes?.[n.id]?.kind ?? 'event'
          }};
        }}),
        edges: edges.get().map(e => {{
          return {{
            id: e.id,
            source: e.from,
            target: e.to,
            label: nodeMeta.edges?.[e.id]?.label ?? null,
            data: nodeMeta.edges?.[e.id]?.prob != null ? {{ prob: nodeMeta.edges[e.id].prob }} : {{}}
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
