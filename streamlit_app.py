import json
import uuid
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – vis-network (no build)", layout="wide")
st.title("🌳 Decision Tree – ComfyUI‑style (right‑click) – vis-network")

# ---------------------------
# Helpers & state
# ---------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

def new_edge_id() -> str:
    return f"e_{uuid.uuid4().hex[:6]}"

if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

# If the front-end pushed us an updated graph through the URL, ingest it.
if "graph" in st.query_params:
    try:
        g = json.loads(st.query_params["graph"])
        # very light validation
        if isinstance(g, dict) and "nodes" in g and "edges" in g:
            st.session_state.graph = g
    except Exception:
        pass
    finally:
        # clear so refreshes don't keep re-importing
        st.query_params.clear()

graph = st.session_state.graph

# ---------------------------
# UI: Import / Export / Clear
# ---------------------------
col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.download_button(
        "💾 Export JSON",
        data=json.dumps(graph, indent=2),
        file_name="decision_tree.json",
        mime="application/json"
    )
with col2:
    uploaded = st.file_uploader("Upload decision_tree.json", type=["json"])
    if uploaded:
        try:
            st.session_state.graph = json.load(uploaded)
            st.success("Imported.")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")
with col3:
    if st.button("🗑 Clear Canvas"):
        st.session_state.graph = {"nodes": [], "edges": []}
        st.rerun()

# Optional debug
with st.expander("Current graph JSON"):
    st.code(json.dumps(st.session_state.graph, indent=2))

# ---------------------------
# Compose the vis-network HTML
# ---------------------------
nodes_js = json.dumps([
    {
        "id": n["id"],
        "label": n["data"]["label"],
        "kind": n.get("kind", "event"),
        # vis options:
        "shape": "box",
        "color": {
            "background": {
                "event":    "#e0ecff",
                "decision": "#e6f7eb",
                "result":   "#fff1e6",
            }.get(n.get("kind", "event"), "#fff"),
            "border": {
                "event":    "#1d4ed8",
                "decision": "#16a34a",
                "result":   "#f97316",
            }.get(n.get("kind", "event"), "#777")
        },
        "borderWidth": 2,
        "margin": 10
    }
    for n in graph["nodes"]
])

edges_js = json.dumps([
    {
        "id": e["id"],
        "from": e["source"],
        "to": e["target"],
        "label": (
            f"{e.get('label') or ''}{' (p='+str(e.get('data', {}).get('prob'))+')' if e.get('data', {}).get('prob') is not None else ''}"
        ).strip()
    } for e in graph["edges"]
])

# Pre-map of id -> kind/label so we can reconstruct data server-side
node_metadata = {n["id"]: {"kind": n.get("kind", "event"), "label": n["data"]["label"]} for n in graph["nodes"]}
edge_metadata = {
    e["id"]: {
        "label": e.get("label"),
        "prob": e.get("data", {}).get("prob")
    }
    for e in graph["edges"]
}

meta_js = json.dumps({"nodes": node_metadata, "edges": edge_metadata})

# Build the full HTML with a custom context menu and sync button
html_block = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>vis-network</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    html, body {{
      height: 100%;
      margin: 0;
      background: #f8fafc;
      font-family: sans-serif;
    }}
    #network {{
      height: 600px;
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
      z-index: 9999;
      padding: 4px 0;
      min-width: 180px;
    }}
    .context-menu button {{
      display: block;
      width: 100%;
      padding: 6px 12px;
      background: transparent;
      border: none;
      text-align: left;
      cursor: pointer;
    }}
    .context-menu button:hover {{
      background: #f1f5f9;
    }}
    .floating-sync {{
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 9000;
      border: none;
      background: #1d4ed8;
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }}
    .floating-sync:hover {{
      background: #2563eb;
    }}
  </style>
</head>
<body>
  <div id="network"></div>
  <button class="floating-sync" id="syncButton" title="Send changes to Streamlit">Sync to Streamlit</button>

  <script>
    // Initial data from Streamlit
    const nodeMeta = {meta_js};
    const originalNodes = {nodes_js};
    const originalEdges = {edges_js};

    // We'll keep a live graph in memory (nodes/edges arrays)
    let nodes = new vis.DataSet(originalNodes);
    let edges = new vis.DataSet(originalEdges);

    // Reconstruct (label, prob) parts from meta, because our 'label' in edges may be merged string
    const edgeMeta = nodeMeta.edges || {{}};

    const container = document.getElementById('network');
    const data = {{
      nodes: nodes,
      edges: edges
    }};
    const options = {{
      interaction: {{
        multiselect: true,
        navigationButtons: true,
        keyboard: true
      }},
      physics: {{
        stabilization: {{
          iterations: 300
        }}
      }},
      edges: {{
        arrows: {{
          to: {{enabled: true}}
        }}
      }}
    }};
    const network = new vis.Network(container, data, options);

    let selectedNode = null;

    // Utility: show context menu
    function showContextMenu(x, y, entries) {{
      hideContextMenu();
      const menu = document.createElement('div');
      menu.className = 'context-menu';
      menu.style.left = x + 'px';
      menu.style.top = y + 'px';

      entries.forEach(e => {{
        const btn = document.createElement('button');
        btn.textContent = e.label;
        btn.onclick = () => {{
          e.action();
          hideContextMenu();
        }};
        menu.appendChild(btn);
      }});

      document.body.appendChild(menu);

      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    function hideContextMenu() {{
      const menu = document.querySelector('.context-menu');
      if (menu) {{
        menu.remove();
      }}
    }}

    // Right-click handler
    container.addEventListener('contextmenu', function(e) {{
      e.preventDefault();
      const pointer = network.getPointer(e);
      const nodeAt = network.getNodeAt(pointer);

      if (!nodeAt) {{
        // Right-click on empty space -> add node menu
        showContextMenu(e.clientX, e.clientY, [
          {{ label: 'Add Event Node', action: () => addNodeAt(pointer.canvas, 'event') }},
          {{ label: 'Add Decision Node', action: () => addNodeAt(pointer.canvas, 'decision') }},
          {{ label: 'Add Result Node', action: () => addNodeAt(pointer.canvas, 'result') }},
          ...(selectedNode ? [
            {{ label: 'Connect selected → click target later', action: () => {{
              alert('Click a target node to connect from ' + selectedNode);
            }}}}
          ] : [])
        ]);
      }} else {{
        // Right-click on a node
        showContextMenu(e.clientX, e.clientY, [
          {{ label: 'Connect from this node', action: () => {{
              selectedNode = nodeAt;
              alert('Selected ' + selectedNode + '. Now right-click a different node to connect.');
          }}}},
          ...(selectedNode && selectedNode !== nodeAt ? [
            {{ label: 'Connect selected → this node', action: () => {{
                connectNodes(selectedNode, nodeAt);
                selectedNode = null;
            }}}}
          ] : []),
          {{ label: 'Edit label', action: () => editNodeLabel(nodeAt) }},
          {{ label: 'Delete node', action: () => deleteNode(nodeAt) }}
        ]);
      }}
    }});

    function addNodeAt(pos, kind) {{
      const id = 'n_' + Math.random().toString(36).substring(2, 8);
      const label = prompt(`Enter {kind} label:`, kind.charAt(0).toUpperCase() + kind.slice(1));
      if (!label) return;

      // store meta
      if (!nodeMeta.nodes) nodeMeta.nodes = {{}};
      nodeMeta.nodes[id] = {{ kind, label }};

      // vis doesn't persist absolute coords (need convert)
      const position = network.canvasToDOM(pos);
      // We can't set exact XY in vis-network DataSet easily post-creation, but we can move them with:
      // network.moveNode(id, x, y) right after add
      nodes.add({{
        id,
        label,
        shape: 'box',
        color: {{
          background: kind === 'event' ? '#e0ecff' :
                      kind === 'decision' ? '#e6f7eb' : '#fff1e6',
          border: kind === 'event' ? '#1d4ed8' :
                  kind === 'decision' ? '#16a34a' : '#f97316'
        }},
        borderWidth: 2,
        margin: 10
      }});
      // Move after small timeout so node exists
      requestAnimationFrame(() => {{
        network.moveNode(id, position.x, position.y);
      }});
    }}

    function editNodeLabel(nodeId) {{
      const node = nodes.get(nodeId);
      const newLabel = prompt('New label:', node.label || '');
      if (newLabel !== null) {{
        nodes.update({{ id: nodeId, label: newLabel }});
        if (!nodeMeta.nodes) nodeMeta.nodes = {{}};
        if (!nodeMeta.nodes[nodeId]) nodeMeta.nodes[nodeId] = {{kind: 'event', label: ''}};
        nodeMeta.nodes[nodeId].label = newLabel;
      }}
    }}

    function deleteNode(nodeId) {{
      // remove node and its edges
      nodes.remove(nodeId);
      const toRemove = edges.get().filter(e => e.from === nodeId || e.to === nodeId).map(e => e.id);
      edges.remove(toRemove);
      if (nodeMeta.nodes && nodeMeta.nodes[nodeId]) delete nodeMeta.nodes[nodeId];
    }}

    function connectNodes(sourceId, targetId) {{
      const label = prompt('Edge label (optional):', '');
      const probStr = prompt('Probability (optional):', '');
      const id = 'e_' + Math.random().toString(36).substring(2, 8);
      edges.add({{
        id: id,
        from: sourceId,
        to: targetId,
        label: (label || '') + (probStr ? (label ? ' ' : '') + '(p=' + probStr + ')' : '')
      }});
      if (!nodeMeta.edges) nodeMeta.edges = {{}};
      nodeMeta.edges[id] = {{ label: label || null, prob: probStr ? parseFloat(probStr) : null }};
    }}

    // Sync button: push the updated graph back to Streamlit via query params
    document.getElementById('syncButton').onclick = function() {{
      // rebuild graph JSON
      const rebuilt = {{
        nodes: nodes.get().map(n => ({{
          id: n.id,
          type: 'default',
          position: {{}}, // unused here
          data: {{ label: nodeMeta.nodes?.[n.id]?.label ?? n.label }},
          kind: nodeMeta.nodes?.[n.id]?.kind ?? 'event'
        }})),
        edges: edges.get().map(e => ({{
          id: e.id,
          source: e.from,
          target: e.to,
          label: nodeMeta.edges?.[e.id]?.label ?? null,
          data: nodeMeta.edges?.[e.id]?.prob != null ? {{ prob: nodeMeta.edges[e.id].prob }} : {{}}
        }}))
      }};
      const payload = encodeURIComponent(JSON.stringify(rebuilt));
      const base = window.location.href.split('?')[0];
      window.location.href = base + '?graph=' + payload;
    };
  </script>
</body>
</html>
"""

components.html(html_block, height=650, scrolling=True)
