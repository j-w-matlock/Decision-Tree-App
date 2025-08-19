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
  addEdge,
  Connection,
} from "reactflow";
import "reactflow/dist/style.css";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import type { NodeData, EdgeData } from "./types";

const deepEqual = (a: any, b: any) => JSON.stringify(a) === JSON.stringify(b);

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
  const prevValue = useRef<any>();
  const debounceRef = useRef<number>();

  const updateStreamlit = useCallback(
    (n: Node<NodeData>[], e: Edge<EdgeData>[]) => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = window.setTimeout(() => {
        Streamlit.setComponentValue({ nodes: n, edges: e });
      }, 300);
    },
    []
  );

  useEffect(() => {
    Streamlit.setFrameHeight();
  });

  useEffect(() => {
    updateStreamlit(nodes, edges);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const value = props.args?.value;
    const previous = prevValue.current;

    if (!value) {
      if (previous) {
        setNodes([]);
        setEdges([]);
        prevValue.current = value;
      }
      return;
    }

    if (!previous || !deepEqual(previous, value)) {
      setNodes((prevNodes) => {
        const prevMap = new Map(prevNodes.map((n) => [n.id, n]));
        const incoming = (value.nodes ?? []) as Node<NodeData>[];
        return incoming.map((n) => {
          const existing = prevMap.get(n.id);
          if (existing) {
            return { ...existing, ...n, position: existing.position };
          }
          return n;
        });
      });

      setEdges((prevEdges) => {
        const prevMap = new Map(prevEdges.map((e) => [e.id, e]));
        const incoming = (value.edges ?? []) as Edge<EdgeData>[];
        return incoming.map((e) => {
          const existing = prevMap.get(e.id);
          return existing ? { ...existing, ...e } : e;
        });
      });

      prevValue.current = value;
    }
  });


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

  const onNodeDragStop = useCallback(() => {
    updateStreamlit(nodes, edges);
  }, [nodes, edges, updateStreamlit]);

  const onEdgeUpdate = useCallback(
    (oldEdge: Edge, newConnection: Connection) => {
      setEdges((eds) => {
        const index = eds.findIndex((e) => e.id === oldEdge.id);
        if (index === -1) return eds;
        const updated = [...eds];
        updated[index] = { ...updated[index], ...newConnection };
        updateStreamlit(nodes, updated);
        return updated;
      });
    },
    [nodes, updateStreamlit]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const updated = addEdge(connection, eds);
        updateStreamlit(nodes, updated);
        return updated;
      });
    },
    [nodes, updateStreamlit]
  );

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      setNodes((nds) => {
        const remaining = nds.filter((n) => !deleted.find((d) => d.id === n.id));
        updateStreamlit(remaining, edges);
        return remaining;
      });
    },
    [edges, updateStreamlit]
  );

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      setEdges((eds) => {
        const remaining = eds.filter((e) => !deleted.find((d) => d.id === e.id));
        updateStreamlit(nodes, remaining);
        return remaining;
      });
    },
    [nodes, updateStreamlit]
  );

  const onMove = useCallback((_, vp: Viewport) => {
    setViewport(vp);
  }, []);

  const uniqueEdges = edges.filter((e, index, arr) => {
    const hasRequired = e.id && e.source && e.target;
    const duplicateIndex = arr.findIndex(
      (other) =>
        other.id === e.id &&
        other.source === e.source &&
        other.target === e.target
    );
    return hasRequired && duplicateIndex === index;
  });

  const styledEdges = uniqueEdges.map((e) => {
    const style: any = { strokeWidth: 2 };
    if ((e as any).color) {
      style.stroke = (e as any).color;
    }
    const markerEnd = (e as any).markerEnd;
    return markerEnd ? { ...e, style, markerEnd } : { ...e, style };
  });

  return (
    <div style={{ width: "100vw", height: "80vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onEdgeUpdate={onEdgeUpdate}
        onConnect={onConnect}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onMove={onMove}
        defaultEdgeOptions={{ style: { strokeWidth: 2 }, type: 'straight' }}
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

