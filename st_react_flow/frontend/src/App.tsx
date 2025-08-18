import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
} from "reactflow";
import "reactflow/dist/style.css";
import { Streamlit, StreamlitComponentBase, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData } from "./types";

class App extends StreamlitComponentBase<any> {
  state = {
    nodes: (this.props.args?.value?.nodes ?? []) as Node<NodeData>[],
    edges: (this.props.args?.value?.edges ?? []) as Edge<EdgeData>[],
  };

  componentDidMount() {
    Streamlit.setFrameHeight();
  }

  componentDidUpdate(prevProps: any, prevState: any) {
    Streamlit.setFrameHeight();
    const prevValue = prevProps.args?.value;
    const currValue = this.props.args?.value;
    if (prevValue !== currValue) {
      this.setState({
        nodes: (currValue?.nodes ?? []) as Node<NodeData>[],
        edges: (currValue?.edges ?? []) as Edge<EdgeData>[],
      });
    }
    if (
      prevState.nodes !== this.state.nodes ||
      prevState.edges !== this.state.edges
    ) {
      Streamlit.setComponentValue({ nodes: this.state.nodes, edges: this.state.edges });
    }
  }

  onNodesChange = (changes: NodeChange[]) => {
    const filtered = changes.filter((c) => c.type !== "remove");
    this.setState((s: any) => ({ nodes: applyNodeChanges(filtered, s.nodes) }));
  };

  onEdgesChange = (changes: EdgeChange[]) => {
    const filtered = changes.filter((c) => c.type !== "remove");
    this.setState((s: any) => ({ edges: applyEdgeChanges(filtered, s.edges) }));
  };

  render() {
    const { nodes, edges } = this.state;
    const styledEdges = edges.map((e) =>
      (e as any).color ? { ...e, style: { stroke: (e as any).color } } : e
    );

    return (
      <div style={{ width: "100vw", height: "80vh" }}>
        <ReactFlow
          nodes={nodes}
          edges={styledEdges}
          onNodesChange={this.onNodesChange}
          onEdgesChange={this.onEdgesChange}
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

