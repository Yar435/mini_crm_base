import { apiJson } from "./client";

export type GraphNode = {
  id: number;
  name: string;
  is_final: boolean;
  /** Порядок статуса в воронке amo (колонки слева направо); null если не задан. */
  sort?: number | null;
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

export type AmoPipelineListItem = {
  id: number;
  name: string;
  sort: number | null;
  is_main: boolean;
};

export async function getPipelines(): Promise<{ pipelines: AmoPipelineListItem[] }> {
  return apiJson<{ pipelines: AmoPipelineListItem[] }>("/analytics/pipelines/", {
    method: "GET",
  });
}

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

export type LeadLinkCoverageResponse = {
  pipeline_id: number;
  coverage: {
    total_leads: number;
    with_contacts: number;
    with_companies: number;
    contact_ratio: number;
    company_ratio: number;
  };
  meta: {
    include_deleted: boolean;
    computed_at: number;
  };
};

export type TopContactsByLeadsResponse = {
  pipeline_id: number;
  top_k: number;
  contacts: Array<{
    contact_id: number;
    leads_count: number;
  }>;
  meta: {
    include_deleted: boolean;
    computed_at: number;
  };
};

export type TopCompaniesByLeadsResponse = {
  pipeline_id: number;
  top_k: number;
  companies: Array<{
    company_id: number;
    leads_count: number;
  }>;
  meta: {
    include_deleted: boolean;
    computed_at: number;
  };
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

export async function getLeadLinkCoverage(
  pipelineId: number,
  includeDeleted = false
): Promise<LeadLinkCoverageResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(pipelineId));
  if (includeDeleted) q.set("include_deleted", "true");
  return apiJson<LeadLinkCoverageResponse>(`/analytics/lead-link-coverage/?${q.toString()}`, {
    method: "GET",
  });
}

export async function getTopContactsByLeads(
  pipelineId: number,
  topK: number,
  includeDeleted = false
): Promise<TopContactsByLeadsResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(pipelineId));
  q.set("top_k", String(topK));
  if (includeDeleted) q.set("include_deleted", "true");
  return apiJson<TopContactsByLeadsResponse>(`/analytics/top-contacts-by-leads/?${q.toString()}`, {
    method: "GET",
  });
}

export async function getTopCompaniesByLeads(
  pipelineId: number,
  topK: number,
  includeDeleted = false
): Promise<TopCompaniesByLeadsResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(pipelineId));
  q.set("top_k", String(topK));
  if (includeDeleted) q.set("include_deleted", "true");
  return apiJson<TopCompaniesByLeadsResponse>(`/analytics/top-companies-by-leads/?${q.toString()}`, {
    method: "GET",
  });
}

export type LeadJourneyTransition = {
  event_id: string;
  at: number;
  from_status_id: number;
  to_status_id: number;
  by_user: number | null;
  in_window: boolean;
  /** Секунды от предыдущего перехода; для первого — от created_at лида, если есть. */
  delta_sec: number | null;
};

export type LeadJourneyStatus = {
  id: number;
  name: string;
  sort: number | null;
};

export type LeadJourneyLead = {
  lead_id: number;
  name: string;
  transitions: LeadJourneyTransition[];
};

export type LeadJourneysResponse = {
  meta: {
    pipeline_id: number;
    as_of_ts: number;
    window_start_ts: number;
    window_end_ts: number;
    window_minutes: number;
    lead_filter: "activity_in_window" | "open_in_pipeline";
    limit: number;
    computed_at: number;
    open_leads_note?: string;
  };
  statuses: LeadJourneyStatus[];
  leads: LeadJourneyLead[];
};

export async function getLeadJourneys(params: {
  pipeline_id: number;
  as_of: string;
  window_minutes: number;
  lead_filter: "activity_in_window" | "open_in_pipeline";
  limit: number;
}): Promise<LeadJourneysResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(params.pipeline_id));
  q.set("as_of", params.as_of);
  q.set("window_minutes", String(params.window_minutes));
  q.set("lead_filter", params.lead_filter);
  q.set("limit", String(params.limit));
  return apiJson<LeadJourneysResponse>(`/analytics/lead-journeys/?${q.toString()}`, {
    method: "GET",
  });
}

export type LeadJourneyIntervalTask = {
  id: number;
  text: string;
  created_at: number | null;
  updated_at: number | null;
  is_completed: boolean | null;
  responsible_user_id: number | null;
};

export type LeadJourneyIntervalResponse = {
  meta: {
    pipeline_id: number;
    lead_id: number;
    from_ts: number;
    to_ts: number;
  };
  tasks: LeadJourneyIntervalTask[];
};

export async function getLeadJourneyInterval(params: {
  pipeline_id: number;
  lead_id: number;
  from_ts: number;
  to_ts: number;
}): Promise<LeadJourneyIntervalResponse> {
  const q = new URLSearchParams();
  q.set("pipeline_id", String(params.pipeline_id));
  q.set("lead_id", String(params.lead_id));
  q.set("from_ts", String(params.from_ts));
  q.set("to_ts", String(params.to_ts));
  return apiJson<LeadJourneyIntervalResponse>(`/analytics/lead-journey-interval/?${q.toString()}`, {
    method: "GET",
  });
}
