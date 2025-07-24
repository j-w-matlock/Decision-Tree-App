import json
import uuid
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Decision Tree – vis-network", layout="wide")
st.title("🌳 Decision Tree – ComfyUI-style (Right-Click Interactive)")

# ---------------------------
# Helpers & state
# ---------------------------
def new_node_id() -> str:
    return f"n_{uuid.uuid4().hex[:6]}"

if "graph" not in st.session_state:
    st.session_state.graph = {"nodes": [], "edges": []}

# Check for graph updates via query_params
if "graph" in st.query_params:
    try:
        g = json.loads(urllib.parse.unquote(st.query_params["graph"]))
        if isinstance(g, dict) and "nodes" in g and "edges" in g:
            st.session_state.graph = g
    except Exception as e:
        st.error(f"Failed to parse graph: {e}")
    finally:
        st.query_params.clear()

graph = st.session_state.graph

# ---------------------------
# UI: Import / Export / Clear
# ---------------------------
col1, col2, col3 = st.columns([1, 1, 1])
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

# Debug view
with st.expander("Current graph JSON"):
    st.code(json.dumps(graph, indent=2))

# ---------------------------
# Compose vis-network HTML
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
            f"{e.get('label') or ''}"
            f"{' (p='+str(e.get('data', {}).get('prob'))+')' if e.get('data', {}).get('prob') is not None else ''}"
        ).strip()
    }
    for e in graph["edges"]
])

node_metadata = {
    n["id"]: {"kind": n.get("kind", "event"), "label": n["data"]["label"]}
    for n in graph["nodes"]
}
edge_metadata = {
    e["id"]: {
        "label": e.get("label"),
        "prob": e.get("data", {}).get("prob")
    }
    for e in graph["edges"]
}
meta_js = json.dumps({"nodes": node_metadata, "edges": edge_metadata})

# ---------------------------
# HTML with highlight + floating label
# ---------------------------
html_block = f"""
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
      font-family: sans-serif;
    }}
    #network {{
      height: 600px;
      background: #f1f5f9;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      position: relative;
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
      z-index: 9000;
    }}
  </style>
</head>
<body>
  <div id="network"></div>
  <button class="floating-sync" id="syncButton">Sync to Streamlit</button>
  <div id="selected-label">Selected node: <span id="selected-node-id"></span></div>

  <script>
    const nodeMeta = {meta_js};
    const nodes = new vis.DataSet({nodes_js});
    const edges = new vis.DataSet({edges_js});

    const container = document.getElementById('network');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {{
      interaction: {{ navigationButtons: true, keyboard: true }},
      physics: {{ stabilization: {{ iterations: 300 }} }},
      edges: {{ arrows: {{ to: {{enabled: true}} }} }},
      nodes: {{
        chosen: {{
          node: (values, id, selected, hovering) => {{
            values.borderWidth = selected ? 4 : 2;
            values.color = values.color || '#e0ecff';
          }}
        }}
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
      entries.forEach(e => {{
        const btn = document.createElement('button');
        btn.textContent = e.label;
        btn.onclick = () => {{ e.action(); hideContextMenu(); }};
        menu.appendChild(btn);
      }});
      document.body.appendChild(menu);
      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    function addNode(kind) {{
      const id = 'n_' + Math.random().toString(36).substring(2, 8);
      const label = prompt('Enter ' + kind + ' label:', kind.charAt(0).toUpperCase() + kind.slice(1));
      if (!label) return;
      nodeMeta.nodes[id] = {{ kind, label }};
      nodes.add({{
        id: id,
        label: label,
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
    }}

    function connectNodes(source, target) {{
      const label = prompt('Edge label (optional):', '');
      const probStr = prompt('Probability (optional):', '');
      const id = 'e_' + Math.random().toString(36).substring(2, 8);
      edges.add({{
        id: id,
        from: source,
        to: target,
        label: (label || '') + (probStr ? ' (p=' + probStr + ')' : '')
      }});
      nodeMeta.edges[id] = {{ label: label || null, prob: probStr ? parseFloat(probStr) : null }};
    }}

    container.addEventListener('contextmenu', function(e) {{
      e.preventDefault();
      const pointer = network.getPointer(e);
      const nodeAt = network.getNodeAt(pointer);
      if (!nodeAt) {{
        showContextMenu(e.clientX, e.clientY, [
          {{ label: 'Add Event Node', action: () => addNode('event') }},
          {{ label: 'Add Decision Node', action: () => addNode('decision') }},
          {{ label: 'Add Result Node', action: () => addNode('result') }}
        ]);
      }} else {{
        showContextMenu(e.clientX, e.clientY, [
          {{ label: 'Select this node', action: () => {{ selectedNode = nodeAt; updateSelectedLabel(); }} }},
          ...(selectedNode && selectedNode !== nodeAt ? [
            {{ label: 'Connect selected → this node', action: () => {{
              connectNodes(selectedNode, nodeAt);
              selectedNode = null;
              updateSelectedLabel();
            }}}}
          ] : [])
        ]);
      }}
    }});

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

components.html(html_block, height=650, scrolling=True)
