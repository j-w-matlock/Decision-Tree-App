export type NodeKind = "decision" | "chance" | "outcome" | "utility";

export interface NodeData {
  label: string;
  kind: NodeKind;
  value?: number;
  cost?: number;
  benefit?: number;
}

export interface EdgeData {
  label?: string;
  prob?: number;
}
