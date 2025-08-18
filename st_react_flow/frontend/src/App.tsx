import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Viewport,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowProvider,
  useReactFlow,
} from "reactflow";
import "reactflow/dist/style.css";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData } from "./types";

const Flow = (props: any) => {
  const [nodes, setNodes] = useState<Node<NodeData>[]>(
    (props.args?.value?.nodes ?? []) as Node<NodeData>[]
  );
  const [edges, setEdges] = useState<Edge<EdgeData>[]>(
    (props.args?.value?.edges ?? []) as Edge<EdgeData>[]
  );
  const [viewport, setViewport] = useState<Viewport | null>(null);
  const reactFlowInstance = useReactFlow();
  const hasFitView = useRef(false);
  const isInitialRender = useRef(true);

  useEffect(() => {
    Streamlit.setFrameHeight();
  });

  useEffect(() => {
    const value = props.args?.value;
    setNodes((value?.nodes ?? []) as Node<NodeData>[]);
    setEdges((value?.edges ?? []) as Edge<EdgeData>[]);
  }, [props.args?.value]);

  useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }
    Streamlit.setComponentValue({ nodes, edges });
  }, [nodes, edges]);

  useEffect(() => {
    if (nodes.length > 0) {
      if (!hasFitView.current && !viewport) {
        reactFlowInstance.fitView();
        setViewport(reactFlowInstance.getViewport());
        hasFitView.current = true;
      } else if (viewport) {
        reactFlowInstance.setViewport(viewport);
      }
    }
  }, [nodes, reactFlowInstance, viewport]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    const filtered = changes.filter((c) => c.type !== "remove");
    setNodes((nds) => applyNodeChanges(filtered, nds));
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    const filtered = changes.filter((c) => c.type !== "remove");
    setEdges((eds) => applyEdgeChanges(filtered, eds));
  }, []);

  const onMove = useCallback((_, vp: Viewport) => {
    setViewport(vp);
  }, []);

  const styledEdges = edges.map((e) =>
    (e as any).color ? { ...e, style: { stroke: (e as any).color } } : e
  );

  return (
    <div style={{ width: "100vw", height: "80vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onMove={onMove}
      >
        <MiniMap />
        <Controls />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

const App = (props: any) => (
  <ReactFlowProvider>
    <Flow {...props} />
  </ReactFlowProvider>
);

export default withStreamlitConnection(App);

