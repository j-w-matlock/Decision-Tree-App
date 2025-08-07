from __future__ import annotations

"""Utility classes for working with decision trees.

The :class:`DecisionTree` class converts the in-memory ``graph`` used by
``streamlit_app.py`` into a structure that can be traversed to produce all
possible decision pathways.  Each pathway lists the ordered steps from the
root node to an end node together with its cumulative probability.

This module is intentionally lightweight and free of any Streamlit
dependencies so that it can be tested and reused independently from the UI.
"""

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Optional


@dataclass
class Node:
    """A single node in the decision tree."""

    id: str
    label: str
    kind: str  # ``decision``, ``chance``, ``outcome`` or ``utility``
    cost: Optional[float] = None
    benefit: Optional[float] = None
    value: Optional[float] = None


@dataclass
class Edge:
    """A connection between two nodes."""

    source: str
    target: str
    label: Optional[str] = None
    prob: Optional[float] = None


@dataclass
class Pathway:
    """A fully qualified path from a root to a leaf node."""

    steps: List[str]
    probability: float
    cost: float = 0.0
    benefit: float = 0.0
    value: float = 0.0


class DecisionTree:
    """A representation of the decision tree and traversal helpers."""

    def __init__(self, nodes: List[Node], edges: List[Edge]):
        self.nodes: Dict[str, Node] = {n.id: n for n in nodes}
        self.edges = edges
        self._outgoing: Dict[str, List[Edge]] = defaultdict(list)
        self._incoming: Dict[str, List[Edge]] = defaultdict(list)
        for e in edges:
            self._outgoing[e.source].append(e)
            self._incoming[e.target].append(e)

    @classmethod
    def from_graph(cls, graph: dict) -> "DecisionTree":
        """Create a :class:`DecisionTree` from a Streamlit ``graph`` dict."""

        nodes = [
            Node(
                id=n["id"],
                label=n["data"]["label"],
                kind=n.get("kind", "chance"),
                cost=n.get("data", {}).get("cost"),
                benefit=n.get("data", {}).get("benefit"),
                value=n.get("data", {}).get("value"),
            )
            for n in graph.get("nodes", [])
        ]
        edges = []
        for e in graph.get("edges", []):
            data = e.get("data", {})
            edges.append(
                Edge(
                    source=e["source"],
                    target=e["target"],
                    label=e.get("label"),
                    prob=data.get("prob"),
                )
            )
        return cls(nodes, edges)

    # ------------------------------------------------------------------
    # Traversal helpers
    # ------------------------------------------------------------------
    def _roots(self) -> List[Node]:
        return [n for n in self.nodes.values() if not self._incoming.get(n.id)]

    def pathways(self) -> List[Pathway]:
        """Return all root-to-leaf paths with cumulative probabilities."""

        results: List[Pathway] = []

        def dfs(node_id: str, path: List[str], prob: float, cost: float, benefit: float, value: float) -> None:
            node = self.nodes[node_id]
            path.append(node.label)
            cost += node.cost or 0.0
            benefit += node.benefit or 0.0
            value += node.value or 0.0
            children = self._outgoing.get(node_id)
            if not children:
                results.append(Pathway(steps=path.copy(), probability=prob, cost=cost, benefit=benefit, value=value))
            else:
                for edge in children:
                    edge_steps = path + ([f"[{edge.label}]"] if edge.label else [])
                    edge_prob = edge.prob if edge.prob is not None else 1.0
                    dfs(edge.target, edge_steps, prob * edge_prob, cost, benefit, value)
            path.pop()

        for root in self._roots():
            dfs(root.id, [], 1.0, 0.0, 0.0, 0.0)
        return results


__all__ = ["Node", "Edge", "Pathway", "DecisionTree"]
