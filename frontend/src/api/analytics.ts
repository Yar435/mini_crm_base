import { apiJson } from "./client";

export type GraphNode = {
  id: number;
  name: string;
  is_final: boolean;
};

export type GraphEdge = {
  from_status_id: number;
  to_status_id: number;
  weight: number;
  avg_time_sec: number | null;
  p_final: number;
};

export type ProcessGraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  meta: {
    pipeline_id: number;
    as_of: number;
    mode: string;
    window_minutes: number | null;
    top_k: number;
    from_status_id: number | null;
    min_price?: number | null;
    max_price?: number | null;
    computed_at: number;
  };
};

export type ProcessGraphParams = {
  pipeline_id: number;
  as_of: string;
  mode: "replay_speed" | "rolling_window";
  window_minutes?: number | null;
  top_k?: number;
  from_status_id?: number | null;
  min_price?: number | null;
  max_price?: number | null;
};

export async function getProcessGraph(params: ProcessGraphParams): Promise<ProcessGraphResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(params.pipeline_id));
  q.set("as_of", params.as_of);
  q.set("mode", params.mode);
  if (params.mode === "rolling_window" && params.window_minutes != null) {
    q.set("window_minutes", String(params.window_minutes));
  }
  if (params.top_k != null) q.set("top_k", String(params.top_k));
  if (params.from_status_id != null) q.set("from_status_id", String(params.from_status_id));
  if (params.min_price != null) q.set("min_price", String(params.min_price));
  if (params.max_price != null) q.set("max_price", String(params.max_price));

  return apiJson<ProcessGraphResponse>(`/analytics/process-graph/?${q.toString()}`, {
    method: "GET",
  });
}
