import dagre from "dagre";
import { Position, type Edge, type Node } from "@xyflow/react";

const NODE_W = 200;
const NODE_H = 52;

function nodeOrderKey(n: Node): number {
  const s = n.data && typeof n.data === "object" && "sort" in n.data ? n.data.sort : null;
  if (typeof s === "number" && Number.isFinite(s)) return s;
  return Number(n.id);
}

/** Если dagre не подошёл — сетка по порядку sort/id (колонки слева направо, перенос строки). */
function fallbackLayoutLR(nodes: Node[]): Node[] {
  const sorted = [...nodes].sort((a, b) => {
    const d = nodeOrderKey(a) - nodeOrderKey(b);
    if (d !== 0) return d;
    return Number(a.id) - Number(b.id);
  });
  const cols = Math.min(6, Math.max(3, Math.ceil(Math.sqrt(sorted.length * 2))));
  const colW = 230;
  const rowH = 88;
  return sorted.map((n, i) => ({
    ...n,
    position: { x: (i % cols) * colW, y: Math.floor(i / cols) * rowH },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  }));
}

/**
 * Иерархический layout слева направо (как этапы воронки). Уменьшает пересечения
 * по сравнению с одной линией по id.
 */
export function layoutWithDagre(nodes: Node[], edges: Edge[]): Node[] {
  if (nodes.length === 0) return nodes;

  try {
    const g = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
    g.setGraph({
      rankdir: "LR",
      ranksep: 78,
      nodesep: 38,
      edgesep: 12,
      marginx: 24,
      marginy: 24,
    });

    for (const n of nodes) {
      g.setNode(n.id, { width: NODE_W, height: NODE_H });
    }
    for (const e of edges) {
      if (g.hasNode(e.source) && g.hasNode(e.target)) {
        g.setEdge(e.source, e.target);
      }
    }

    dagre.layout(g);

    return nodes.map((node) => {
      const p = g.node(node.id);
      if (!p || typeof p.x !== "number" || typeof p.y !== "number") {
        return { ...node, position: { x: 0, y: 0 } };
      }
      return {
        ...node,
        position: {
          x: p.x - NODE_W / 2,
          y: p.y - NODE_H / 2,
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
    });
  } catch {
    return fallbackLayoutLR(nodes);
  }
}

export const PROCESS_NODE_SIZE = { w: NODE_W, h: NODE_H };
