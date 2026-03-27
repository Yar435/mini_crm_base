import { useCallback, useEffect, useState, type MouseEvent } from "react";
import {
  Background,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  getLeadJourneyInterval,
  type LeadJourneyIntervalTask,
  type LeadJourneyLead,
  type LeadJourneyStatus,
} from "../api/analytics";
import { ApiError } from "../api/client";
import { formatDurationSec, formatUnixTsRu } from "../utils/timeFormat";

const GAP = 130;

type NodeData = { label: string; stepIndex: number; role: "from" | "to" };
type EdgeData = { stepIndex: number };

type Selection =
  | { kind: "edge"; stepIndex: number }
  | { kind: "node"; stepIndex: number; role: "from" | "to" }
  | null;

function statusMap(statuses: LeadJourneyStatus[]): Map<number, LeadJourneyStatus> {
  return new Map(statuses.map((s) => [s.id, s]));
}

function buildNodesAndEdges(lead: LeadJourneyLead, statuses: LeadJourneyStatus[]): {
  nodes: Node<NodeData>[];
  edges: Edge<EdgeData>[];
} {
  const sm = statusMap(statuses);
  const nodes: Node<NodeData>[] = [];
  const edges: Edge<EdgeData>[] = [];
  if (lead.transitions.length === 0) {
    return { nodes, edges };
  }

  let x = 0;
  for (let i = 0; i < lead.transitions.length; i++) {
    const t = lead.transitions[i]!;
    const fromName = sm.get(t.from_status_id)?.name ?? String(t.from_status_id);
    const toName = sm.get(t.to_status_id)?.name ?? String(t.to_status_id);
    const inW = t.in_window;
    const nodeStyle = inW
      ? { border: "2px solid #22c55e", background: "#14532d", color: "#f0fdf4" }
      : { border: "1px solid #64748b", background: "#1e293b", color: "#e2e8f0" };
    const edgeStyle = inW
      ? { stroke: "#22c55e", strokeWidth: 2.5 }
      : { stroke: "#64748b", strokeWidth: 1.5 };

    const fromId = `L${lead.lead_id}-${i}-a`;
    const toId = `L${lead.lead_id}-${i}-b`;
    const shortLabel = formatDurationSec(t.delta_sec);
    nodes.push({
      id: fromId,
      position: { x, y: 0 },
      data: { label: fromName, stepIndex: i, role: "from" },
      style: { ...nodeStyle, fontWeight: 500, padding: 8, borderRadius: 6, minWidth: 96 },
    });
    x += GAP;
    nodes.push({
      id: toId,
      position: { x, y: 0 },
      data: { label: toName, stepIndex: i, role: "to" },
      style: { ...nodeStyle, fontWeight: 500, padding: 8, borderRadius: 6, minWidth: 96 },
    });
    x += GAP;
    edges.push({
      id: `e-${lead.lead_id}-${i}`,
      source: fromId,
      target: toId,
      type: "smoothstep",
      style: edgeStyle,
      data: { stepIndex: i },
      label: shortLabel,
      labelStyle: { fill: "#cbd5e1", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#0f172a", fillOpacity: 0.9 },
      labelShowBg: true,
    });
  }

  return { nodes, edges };
}

function Inner({
  lead,
  statuses,
  pipelineId,
}: {
  lead: LeadJourneyLead;
  statuses: LeadJourneyStatus[];
  pipelineId: number | null;
}) {
  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge<EdgeData>>([]);
  const [selection, setSelection] = useState<Selection>(null);
  const [intervalTasks, setIntervalTasks] = useState<LeadJourneyIntervalTask[] | null>(null);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState<string | null>(null);

  useEffect(() => {
    const { nodes: n, edges: e } = buildNodesAndEdges(lead, statuses);
    setNodes(n);
    setEdges(e);
    setSelection(null);
    setIntervalTasks(null);
    setTasksError(null);
  }, [lead, statuses, setNodes, setEdges]);

  useEffect(() => {
    if (!nodes.length) return;
    const id = requestAnimationFrame(() => fitView({ padding: 0.15, duration: 200 }));
    return () => cancelAnimationFrame(id);
  }, [nodes.length, fitView]);

  useEffect(() => {
    if (!pipelineId || selection?.kind !== "edge") {
      setIntervalTasks(null);
      setTasksError(null);
      setTasksLoading(false);
      return;
    }
    const i = selection.stepIndex;
    const t = lead.transitions[i];
    if (!t) return;
    const fromTs = i > 0 ? lead.transitions[i - 1]!.at : 0;
    const toTs = t.at;
    let cancelled = false;
    setTasksLoading(true);
    setTasksError(null);
    setIntervalTasks(null);
    (async () => {
      try {
        const res = await getLeadJourneyInterval({
          pipeline_id: pipelineId,
          lead_id: lead.lead_id,
          from_ts: fromTs,
          to_ts: toTs,
        });
        if (!cancelled) setIntervalTasks(res.tasks);
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof ApiError ? err.message : String(err);
          setTasksError(msg);
          setIntervalTasks(null);
        }
      } finally {
        if (!cancelled) setTasksLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [pipelineId, selection, lead.lead_id, lead.transitions]);

  const onEdgeClick = useCallback(
    (_: MouseEvent, edge: Edge<EdgeData>) => {
      const si = edge.data?.stepIndex;
      if (si === undefined) return;
      setSelection({ kind: "edge", stepIndex: si });
    },
    []
  );

  const onNodeClick = useCallback((_: MouseEvent, node: Node<NodeData>) => {
    const d = node.data;
    if (d?.stepIndex === undefined || !d.role) return;
    setSelection({ kind: "node", stepIndex: d.stepIndex, role: d.role });
  }, []);

  const onPaneClick = useCallback(() => {
    setSelection(null);
  }, []);

  const sm = statusMap(statuses);

  if (lead.transitions.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded border border-dashed border-slate-600 text-xs text-slate-500">
        Нет переходов в воронке до среза
      </div>
    );
  }

  const detailBlock = (() => {
    if (!selection) {
      return (
        <p className="text-xs text-slate-500">
          Кликните по ребру или блоку статуса — покажем детали. По ребру дополнительно загружаются задачи в
          интервале между переходами.
        </p>
      );
    }
    if (selection.kind === "edge") {
      const i = selection.stepIndex;
      const tr = lead.transitions[i];
      if (!tr) return null;
      const prevAt = i > 0 ? lead.transitions[i - 1]!.at : null;
      return (
        <div className="space-y-2 text-xs text-slate-300">
          <p className="font-semibold text-slate-200">Переход {i + 1}</p>
          <p>
            <span className="text-slate-500">Время:</span> {formatUnixTsRu(tr.at)}
          </p>
          <p>
            <span className="text-slate-500">Δ от предыдущего:</span> {formatDurationSec(tr.delta_sec)}
          </p>
          {prevAt !== null ? (
            <p className="text-slate-500">
              Предыдущее событие: {formatUnixTsRu(prevAt)} → интервал задач (from_ts, to_ts] = ({prevAt},{" "}
              {tr.at}]
            </p>
          ) : (
            <p className="text-slate-500">Первый переход: интервал задач от 0 до {tr.at}</p>
          )}
          <p>
            <span className="text-slate-500">Из:</span>{" "}
            {sm.get(tr.from_status_id)?.name ?? tr.from_status_id} →{" "}
            <span className="text-slate-500">в:</span> {sm.get(tr.to_status_id)?.name ?? tr.to_status_id}
          </p>
          <p>
            <span className="text-slate-500">by_user:</span> {tr.by_user ?? "—"} ·{" "}
            <span className="text-slate-500">event_id:</span> {tr.event_id}
          </p>
          <p>
            <span className="text-slate-500">В окне среза:</span> {tr.in_window ? "да" : "нет"}
          </p>
          <div className="border-t border-slate-700 pt-2">
            <p className="mb-1 font-medium text-slate-200">Задачи в интервале</p>
            {tasksLoading ? (
              <p className="text-slate-500">Загрузка…</p>
            ) : tasksError ? (
              <p className="text-amber-200/90">{tasksError}</p>
            ) : intervalTasks && intervalTasks.length === 0 ? (
              <p className="text-slate-500">Нет задач с меткой времени в интервале</p>
            ) : (
              <ul className="max-h-32 list-inside list-disc space-y-1 overflow-y-auto text-slate-400">
                {(intervalTasks ?? []).map((task) => (
                  <li key={task.id}>
                    #{task.id} {task.text ? `— ${task.text.slice(0, 120)}` : ""}
                    {task.is_completed === true ? " (выполнена)" : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      );
    }
    const tr = lead.transitions[selection.stepIndex];
    if (!tr) return null;
    const name =
      selection.role === "from"
        ? sm.get(tr.from_status_id)?.name ?? String(tr.from_status_id)
        : sm.get(tr.to_status_id)?.name ?? String(tr.to_status_id);
    return (
      <div className="space-y-1 text-xs text-slate-300">
        <p className="font-semibold text-slate-200">
          Узел «{name}» ({selection.role === "from" ? "до" : "после"} перехода {selection.stepIndex + 1})
        </p>
        <p>
          Время перехода на этом шаге: {formatUnixTsRu(tr.at)}
        </p>
        <p className="text-slate-500">
          Повторяющиеся названия статусов — разные моменты времени в истории сделки.
        </p>
      </div>
    );
  })();

  return (
    <div className="space-y-2">
      <div className="h-40 w-full rounded border border-slate-800 bg-slate-950">
        <ReactFlow
          className="lead-journey-mini"
          colorMode="dark"
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onEdgeClick={onEdgeClick}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          edgesFocusable
          nodesFocusable
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
          preventScrolling
          proOptions={{ hideAttribution: true }}
          minZoom={0.4}
          maxZoom={1.2}
        >
          <Background gap={12} color="#1e293b" />
        </ReactFlow>
      </div>
      <div className="rounded border border-slate-700 bg-slate-900/60 p-3">{detailBlock}</div>
    </div>
  );
}

export function LeadJourneyChain({
  lead,
  statuses,
  pipelineId,
}: {
  lead: LeadJourneyLead;
  statuses: LeadJourneyStatus[];
  /** Для загрузки задач по клику на ребро; без pipeline задачи не запрашиваются */
  pipelineId?: number | null;
}) {
  return (
    <ReactFlowProvider>
      <Inner lead={lead} statuses={statuses} pipelineId={pipelineId ?? null} />
    </ReactFlowProvider>
  );
}
