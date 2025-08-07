import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  MarkerType,
  Connection,
  Node,
  Edge
} from "reactflow";
import "reactflow/dist/style.css";
import { nanoid } from "nanoid";
import { Streamlit, StreamlitComponentBase, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData, NodeKind } from "./types";
import type { CSSProperties } from "react";

type Graph = { nodes: Node<NodeData>[]; edges: Edge<EdgeData>[] };

function color(kind: NodeKind) {
  switch (kind) {
    case "chance":
      return "#1d4ed8";
    case "decision":
      return "#16a34a";
    case "outcome":
      return "#f97316";
    case "utility":
      return "#eab308";
    default:
      return "#777";
  }
}

function shapeStyle(kind: NodeKind): CSSProperties {
  const base: CSSProperties = {
    border: `2px solid ${color(kind)}`,
    background: "#fff",
    width: 150,
    height: 150,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };
  switch (kind) {
    case "chance":
      return { ...base, borderRadius: "50%" };
    case "outcome":
      return { ...base, clipPath: "polygon(50% 0, 0 100%, 100% 100%)" };
    case "utility":
      return { ...base, clipPath: "polygon(50% 0, 100% 50%, 50% 100%, 0 50%)" };
    default:
      return base;
  }
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
      style: shapeStyle(kind),
    };
    this.setState((s: any) => ({ nodes: [...s.nodes, node] }));
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
          <button onClick={() => this.addNode("decision")}>+ Decision</button>
          <button onClick={() => this.addNode("chance")}>+ Chance</button>
          <button onClick={() => this.addNode("outcome")}>+ Outcome</button>
          <button onClick={() => this.addNode("utility")}>+ Utility</button>
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
          onNodesChange={(changes) => this.setState({ nodes: changes })}
          onEdgesChange={(changes) => this.setState({ edges: changes })}
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
