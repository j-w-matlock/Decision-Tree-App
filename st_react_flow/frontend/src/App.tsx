import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  MarkerType,
  Connection,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { nanoid } from "nanoid";
import { Streamlit, StreamlitComponentBase, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData } from "./types";

class App extends StreamlitComponentBase<any> {
  state = {
    nodes: (this.props.args?.value?.nodes ?? []) as Node<NodeData>[],
    edges: (this.props.args?.value?.edges ?? []) as Edge<EdgeData>[],
  };

  reactFlowInstance: ReactFlowInstance | null = null;

  componentDidMount() {
    Streamlit.setFrameHeight();
  }

  componentDidUpdate(prevProps: any, prevState: any) {
    Streamlit.setFrameHeight();
    if (
      prevState.nodes !== this.state.nodes ||
      prevState.edges !== this.state.edges
    ) {
      Streamlit.setComponentValue({ nodes: this.state.nodes, edges: this.state.edges });
    }
  }

  onNodesChange = (changes: NodeChange[]) => {
    this.setState((s: any) => ({ nodes: applyNodeChanges(changes, s.nodes) }));
  };

  onEdgesChange = (changes: EdgeChange[]) => {
    this.setState((s: any) => ({ edges: applyEdgeChanges(changes, s.edges) }));
  };

  onConnect = (conn: Connection) => {
    const e: Edge<EdgeData> = {
      ...conn,
      id: nanoid(),
      markerEnd: { type: MarkerType.ArrowClosed },
    } as any;
    this.setState((s: any) => ({ edges: addEdge(e, s.edges) }));
  };

  onPaneContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    if (!this.reactFlowInstance) return;
    const position = this.reactFlowInstance.project({ x: event.clientX, y: event.clientY });
    const node: Node<NodeData> = {
      id: nanoid(),
      type: "default",
      position,
      data: { label: "New node" },
    };
    this.setState((s: any) => ({ nodes: [...s.nodes, node] }));
  };

  render() {
    const { nodes, edges } = this.state;

    return (
      <div style={{ width: "100vw", height: "80vh" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={this.onNodesChange}
          onEdgesChange={this.onEdgesChange}
          onConnect={this.onConnect}
          onInit={(rf) => (this.reactFlowInstance = rf)}
          onPaneContextMenu={this.onPaneContextMenu}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
    );
  }
}

export default withStreamlitConnection(App);

