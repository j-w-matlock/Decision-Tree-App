import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  Connection,
  Node,
  Edge
} from "reactflow";
import "reactflow/dist/style.css";
import { nanoid } from "nanoid";
import { Streamlit, StreamlitComponentBase, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData, NodeKind } from "./types";

type Graph = { nodes: Node<NodeData>[]; edges: Edge<EdgeData>[] };

function color(kind: NodeKind) {
  return kind === "event" ? "#1d4ed8" : kind === "decision" ? "#16a34a" : "#f97316";
}

class App extends StreamlitComponentBase<any> {
  state = {
    nodes: (this.props.args?.value?.nodes ?? []) as Node<NodeData>[],
    edges: (this.props.args?.value?.edges ?? []) as Edge<EdgeData>[],
  };

  componentDidMount() {
    Streamlit.setFrameHeight();
  }

  componentDidUpdate() {
    Streamlit.setFrameHeight();
    Streamlit.setComponentValue({ nodes: this.state.nodes, edges: this.state.edges });
  }

  addNode = (kind: NodeKind) => {
    const node: Node<NodeData> = {
      id: nanoid(),
      type: "default",
      position: { x: 200, y: 100 },
      data: { label: `${kind} node`, kind },
      style: { border: `2px solid ${color(kind)}`, background: "#fff", minWidth: 150 }
    };
    this.setState((s: any) => ({ nodes: [...s.nodes, node] }));
  };

  onNodesChange = (changes: any) => {
    this.setState((s: any) => ({ nodes: changes(s.nodes) })); // reactflow v11 helper
  };

  onEdgesChange = (changes: any) => {
    this.setState((s: any) => ({ edges: changes(s.edges) }));
  };

  onConnect = (conn: Connection) => {
    const e: Edge<EdgeData> = {
      ...conn,
      id: nanoid(),
      markerEnd: { type: MarkerType.ArrowClosed }
    } as any;
    this.setState((s: any) => ({ edges: addEdge(e, s.edges) }));
  };

  render() {
    const { nodes, edges } = this.state;

    return (
      <div style={{ width: "100vw", height: "80vh" }}>
        <div className="toolbar">
          <button onClick={() => this.addNode("event")}>+ Event</button>
          <button onClick={() => this.addNode("decision")}>+ Decision</button>
          <button onClick={() => this.addNode("result")}>+ Result</button>
          <a
            href={`data:application/json,${encodeURIComponent(JSON.stringify({ nodes, edges }, null, 2))}`}
            download="decision_tree.json"
          >
            💾 Export JSON
          </a>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={(c) => this.setState({ nodes: c(nodes) })}   {/* simple wrapper */}
          onEdgesChange={(c) => this.setState({ edges: c(edges) })}
          onConnect={this.onConnect}
          fitView
        >
          <MiniMap nodeStrokeWidth={3} />
          <Controls />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
    );
  }
}

export default withStreamlitConnection(App);
