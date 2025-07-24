export type NodeKind = "event" | "decision" | "result";

export interface NodeData {
  label: string;
  kind: NodeKind;
}

export interface EdgeData {
  label?: string;
  prob?: number;
}
