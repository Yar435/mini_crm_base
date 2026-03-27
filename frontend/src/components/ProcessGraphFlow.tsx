import { useCallback, useEffect, useState, type MouseEvent } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./ProcessGraphFlow.css";
import type { ProcessGraphResponse } from "../api/analytics";
import { layoutWithDagre } from "./processGraphLayout";

function formatDuration(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) return "";
  if (sec < 60) return `${Math.round(sec)} с`;
  if (sec < 3600) return `${Math.round(sec / 60)} мин`;
  return `${(sec / 3600).toFixed(1)} ч`;
}

type MetricEdgeData = {
  weight: number;
  pFinal: number;
  avgSec: number | null;
  shortLabel: string;
  fullLabel: string;
};

function graphToFlow(data: ProcessGraphResponse): { nodes: Node[]; edges: Edge<MetricEdgeData>[] } {
  const sorted = [...data.nodes].sort((a, b) => {
    const sa = a.sort ?? a.id;
    const sb = b.sort ?? b.id;
    return sa - sb;
  });

  const nodes: Node[] = sorted.map((n) => ({
    id: String(n.id),
    type: "default",
    position: { x: 0, y: 0 },
    style: { fontWeight: 500 },
    data: {
      label: `${n.name}${n.is_final ? " ✓" : ""}`,
      sort: n.sort ?? null,
    },
  }));

  const maxW = Math.max(...data.edges.map((e) => e.weight), 1);

  const edges: Edge<MetricEdgeData>[] = data.edges.map((e, i) => {
    const avg =
      e.avg_time_sec != null ? ` · среднее время: ${formatDuration(e.avg_time_sec)}` : "";
    const pPct = (e.p_final * 100).toFixed(0);
    const fullLabel = `переходов: ${e.weight} · до финала: ${pPct}%${avg}`;
    const shortLabel = String(e.weight);
    const strokeW = 1 + (e.weight / maxW) * 3.5;
    return {
      id: `e-${e.from_status_id}-${e.to_status_id}-${i}`,
      type: "smoothstep",
      source: String(e.from_status_id),
      target: String(e.to_status_id),
      label: shortLabel,
      animated: false,
      style: { stroke: "#94a3b8", strokeWidth: strokeW },
      labelStyle: { fill: "#e2e8f0", fontWeight: 600, fontSize: 11 },
      labelBgStyle: { fill: "#0f172a", fillOpacity: 0.92 },
      labelShowBg: true,
      data: {
        weight: e.weight,
        pFinal: e.p_final,
        avgSec: e.avg_time_sec,
        shortLabel,
        fullLabel,
      },
    };
  });

  return { nodes, edges };
}

function applyEdgeLabelMode(
  edges: Edge<MetricEdgeData>[],
  compact: boolean
): Edge<MetricEdgeData>[] {
  return edges.map((edge) => ({
    ...edge,
    label: compact ? edge.data?.shortLabel ?? "" : edge.data?.fullLabel ?? "",
    labelStyle: compact
      ? { fill: "#cbd5e1", fontWeight: 700, fontSize: 12 }
      : { fill: "#e2e8f0", fontWeight: 500, fontSize: 10 },
  }));
}

type Props = {
  data: ProcessGraphResponse | null;
};

function ProcessGraphInner({ data }: Props) {
  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge<MetricEdgeData>>([]);
  const [compactLabels, setCompactLabels] = useState(true);
  const [showMinimap, setShowMinimap] = useState(false);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  useEffect(() => {
    if (!data) {
      setNodes([]);
      setEdges([]);
      setSelectedEdgeId(null);
      return;
    }
    const { nodes: rawNodes, edges: rawEdges } = graphToFlow(data);
    const layouted = layoutWithDagre(rawNodes, rawEdges);
    setNodes(layouted);
    setEdges(applyEdgeLabelMode(rawEdges, compactLabels));
  }, [data, compactLabels, setNodes, setEdges]);

  useEffect(() => {
    if (!nodes.length || !data) return;
    const id = requestAnimationFrame(() => {
      fitView({ padding: 0.12, duration: 220 });
    });
    return () => cancelAnimationFrame(id);
  }, [data, nodes.length, fitView]);

  const onEdgeClick = useCallback((_: MouseEvent, edge: Edge<MetricEdgeData>) => {
    setSelectedEdgeId(edge.id);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedEdgeId(null);
  }, []);

  const selectedEdge = edges.find((e) => e.id === selectedEdgeId);

  if (!data || data.nodes.length === 0) {
    return (
      <div className="flex h-[480px] items-center justify-center rounded-lg border border-dashed border-slate-600 text-slate-500">
        Нет данных для отображения (пустой граф или не загружено)
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs leading-relaxed text-slate-500">
        Показаны до <strong className="text-slate-400">{data.meta.top_k}</strong> самых частых
        переходов между статусами (не вся возможная сеть). Узлы расставлены автоматически слева направо;
        толщина линии — относительная частота перехода. Чтобы уменьшить «паутину», снизьте{" "}
        <span className="text-slate-400">top_k</span> в форме (он ограничивает и граф, и топы). В API
        можно сузить граф параметром <span className="font-mono text-slate-400">from_status_id</span>.
      </p>

      <div className="process-graph-flow h-[min(640px,70vh)] min-h-[420px] w-full overflow-hidden rounded-lg border border-slate-700 bg-slate-950">
        <ReactFlow
          className="process-graph-flow"
          colorMode="dark"
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          minZoom={0.15}
          maxZoom={1.6}
          proOptions={{ hideAttribution: true }}
          elevateEdgesOnSelect
        >
          <Background gap={16} color="#334155" />
          <Controls
            className="process-graph-controls !border-slate-600 !bg-slate-900/95 !shadow-lg"
            showInteractive={false}
          />
          {showMinimap ? (
            <MiniMap
              className="!border-slate-600 !bg-slate-900/90"
              nodeStrokeWidth={3}
              maskColor="rgba(15, 23, 42, 0.75)"
              style={{ width: 140, height: 100, backgroundColor: "#020617" }}
              zoomable
              pannable
            />
          ) : null}
        </ReactFlow>
      </div>

      <div className="flex flex-wrap items-start gap-4 rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2 text-xs text-slate-400">
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            className="rounded border-slate-600 bg-slate-900"
            checked={compactLabels}
            onChange={(e) => setCompactLabels(e.target.checked)}
          />
          Краткие подписи на рёбрах (только число переходов)
        </label>
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            className="rounded border-slate-600 bg-slate-900"
            checked={showMinimap}
            onChange={(e) => setShowMinimap(e.target.checked)}
          />
          Мини-карта
        </label>
      </div>

      {selectedEdge?.data ? (
        <div className="rounded-lg border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-slate-200">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Выбранное ребро</p>
          <p className="mt-1 text-slate-300">{selectedEdge.data.fullLabel}</p>
          <p className="mt-1 font-mono text-xs text-slate-500">
            {selectedEdge.source} → {selectedEdge.target}
          </p>
        </div>
      ) : (
        <p className="text-xs text-slate-500">Кликните по линии перехода — покажем полный текст метрик.</p>
      )}
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
