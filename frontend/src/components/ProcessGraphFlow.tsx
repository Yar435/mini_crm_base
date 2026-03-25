import { useEffect } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { ProcessGraphResponse } from "../api/analytics";

function graphToFlow(data: ProcessGraphResponse): { nodes: Node[]; edges: Edge[] } {
  const sorted = [...data.nodes].sort((a, b) => a.id - b.id);
  const nodes: Node[] = sorted.map((n, i) => ({
    id: String(n.id),
    type: "default",
    position: { x: i * 220, y: 0 },
    data: {
      label: `${n.name}${n.is_final ? " ✓" : ""}`,
    },
  }));

  const edges: Edge[] = data.edges.map((e, i) => {
    const avg =
      e.avg_time_sec != null ? ` · avg ${Math.round(e.avg_time_sec)}s` : "";
    return {
      id: `e-${e.from_status_id}-${e.to_status_id}-${i}`,
      source: String(e.from_status_id),
      target: String(e.to_status_id),
      label: `w=${e.weight} · p=${e.p_final.toFixed(2)}${avg}`,
    };
  });

  return { nodes, edges };
}

type Props = {
  data: ProcessGraphResponse | null;
};

function ProcessGraphInner({ data }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (!data) {
      setNodes([]);
      setEdges([]);
      return;
    }
    const { nodes: n, edges: e } = graphToFlow(data);
    setNodes(n);
    setEdges(e);
  }, [data, setNodes, setEdges]);

  if (!data || data.nodes.length === 0) {
    return (
      <div className="flex h-[480px] items-center justify-center rounded-lg border border-dashed border-slate-600 text-slate-500">
        Нет данных для отображения (пустой граф или не загружено)
      </div>
    );
  }

  return (
    <div className="h-[560px] w-full rounded-lg border border-slate-700 bg-slate-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}

export function ProcessGraphFlow({ data }: Props) {
  return (
    <ReactFlowProvider>
      <ProcessGraphInner data={data} />
    </ReactFlowProvider>
  );
}
