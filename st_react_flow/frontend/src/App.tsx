import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
  Connection
} from "reactflow";
import "reactflow/dist/style.css";
import { nanoid } from "nanoid";
import type { NodeData, EdgeData, NodeKind } from "./types";

declare global {
  interface Window {
    Streamlit?: any;
    parent: any;
  }
}

type Graph = { nodes: Node<NodeData>[]; edges: Edge<EdgeData>[] };

// ---- Streamlit protocol helpers
function sendToStreamlit(type: string, data: any) {
  window.parent.postMessage({ isStreamlitMessage: true, type, data }, "*");
}

function useStreamlitValue<T>(initial: T): [T, (v: T) => void] {
  const [value, setValue] = React.useState<T>(initial);
  React.useEffect(() => {
    function onMessage(event: MessageEvent) {
      const msg = event.data;
      if (msg?.type === "streamlit:setComponentValue") {
        // ignore
      }
      if (msg?.type === "streamlit:render") {
        const v = msg.args?.value ?? initial;
        setValue(v);
      }
    }
    window.addEventListener("message", onMessage);
    sendToStreamlit("streamlit:componentReady", { });
    return () => window.removeEventListener("message", onMessage);
  }, []);
  return [value, (v: T) => {
    setValue(v);
    sendToStreamlit("streamlit:setComponentValue", v);
  }];
}

// ----- Color by node kind
function color(kind: NodeKind) {
  return kind === "event" ? "#1d4ed8" : kind === "decision" ? "#16a34a" : "#f97316";
}

export default function App() {
  const [graph, setGraph] = useStreamlitValue<Graph>({ nodes: [], edges: [] });

  const [nodes, setNodes, onNodesChange] = useNodesState(graph.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graph.edges);

  // keep streamlit in sync
  React.useEffect(() => {
    setGraph({ nodes, edges });
  }, [nodes, edges]);

  const addNode = (kind: NodeKind) => {
    const id = nanoid();
    const node: Node<NodeData> = {
      id,
      type: "default",
      position: { x: 200, y: 100 },
      data: { label: `${kind} node`, kind },
      style: { border: `2px solid ${color(kind)}`, background: "#fff", minWidth: 150 }
    };
    setNodes(nds => nds.concat(node));
  };

  const onConnect = (conn: Connection) => {
    const e: Edge<EdgeData> = {
      ...conn,
      id: nanoid(),
      markerEnd: { type: MarkerType.ArrowClosed }
    } as any;
    setEdges(eds => addEdge(e, eds));
  };

  const Toolbar = () => (
    <div className="toolbar">
      <button onClick={() => addNode("event")}>+ Event</button>
      <button onClick={() => addNode("decision")}>+ Decision</button>
      <button onClick={() => addNode("result")}>+ Result</button>
      <a
        href={`data:application/json,${encodeURIComponent(JSON.stringify({ nodes, edges }, null, 2))}`}
        download="decision_tree.json"
      >💾 Export JSON</a>
    </div>
  );

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <Toolbar />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onConnect={onConnect}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <MiniMap nodeStrokeWidth={3} />
        <Controls />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
