import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProcessGraph, type ProcessGraphResponse } from "../api/analytics";
import { logout } from "../api/auth";
import { ApiError } from "../api/client";
import { ProcessGraphFlow } from "../components/ProcessGraphFlow";

export function ProcessGraphPage() {
  const navigate = useNavigate();
  const [pipelineId, setPipelineId] = useState("1");
  const [asOf, setAsOf] = useState(String(Math.floor(Date.now() / 1000)));
  const [mode, setMode] = useState<"replay_speed" | "rolling_window">("replay_speed");
  const [windowMinutes, setWindowMinutes] = useState("30");
  const [topK, setTopK] = useState("20");
  const [graph, setGraph] = useState<ProcessGraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setGraph(null);
    try {
      const pid = Number(pipelineId);
      if (Number.isNaN(pid)) throw new Error("pipeline_id должен быть числом");
      const w = mode === "rolling_window" ? Number(windowMinutes) : null;
      if (mode === "rolling_window" && (Number.isNaN(w!) || w! <= 0)) {
        throw new Error("Укажите window_minutes > 0 для rolling_window");
      }
      const tk = Number(topK);
      const data = await getProcessGraph({
        pipeline_id: pid,
        as_of: asOf.trim(),
        mode,
        window_minutes: w ?? undefined,
        top_k: Number.isNaN(tk) ? undefined : tk,
      });
      setGraph(data);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="mx-auto max-w-6xl p-4">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-slate-100">Граф процессов</h1>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          Выйти
        </button>
      </header>

      <form
        onSubmit={onSubmit}
        className="mb-6 grid gap-4 rounded-lg border border-slate-700 bg-slate-900/50 p-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <label className="text-sm text-slate-300">
          pipeline_id
          <input
            type="text"
            value={pipelineId}
            onChange={(e) => setPipelineId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
            required
          />
        </label>
        <label className="text-sm text-slate-300 sm:col-span-2">
          as_of (unix или ISO)
          <input
            type="text"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
            required
          />
        </label>
        <label className="text-sm text-slate-300">
          mode
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as "replay_speed" | "rolling_window")}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
          >
            <option value="replay_speed">replay_speed</option>
            <option value="rolling_window">rolling_window</option>
          </select>
        </label>
        <label className="text-sm text-slate-300">
          window_minutes
          <input
            type="text"
            value={windowMinutes}
            onChange={(e) => setWindowMinutes(e.target.value)}
            disabled={mode !== "rolling_window"}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 disabled:opacity-40"
            placeholder="для rolling_window"
          />
        </label>
        <label className="text-sm text-slate-300">
          top_k
          <input
            type="text"
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
          />
        </label>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-sky-600 py-2 font-medium text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? "Загрузка…" : "Загрузить граф"}
          </button>
        </div>
      </form>

      {error ? (
        <p className="mb-4 rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      ) : null}

      {graph ? (
        <pre className="mb-4 max-h-32 overflow-auto rounded border border-slate-700 bg-slate-950/80 p-3 text-xs text-slate-400">
          {JSON.stringify(graph.meta, null, 2)}
        </pre>
      ) : null}

      <ProcessGraphFlow data={graph} />
    </div>
  );
}
