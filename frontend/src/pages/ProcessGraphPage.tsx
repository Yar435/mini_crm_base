import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getLeadJourneys,
  getLeadLinkCoverage,
  getPipelines,
  getProcessGraph,
  getTopCompaniesByLeads,
  getTopContactsByLeads,
  type AmoPipelineListItem,
  type LeadJourneysResponse,
  type LeadLinkCoverageResponse,
  type ProcessGraphResponse,
  type TopCompaniesByLeadsResponse,
  type TopContactsByLeadsResponse,
} from "../api/analytics";
import { logout } from "../api/auth";
import { ApiError } from "../api/client";
import { LeadJourneyChain } from "../components/LeadJourneyChain";
import { ProcessGraphFlow } from "../components/ProcessGraphFlow";

function toDatetimeLocalValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function datetimeLocalToAsOfParam(s: string): string {
  const t = new Date(s).getTime();
  if (Number.isNaN(t)) throw new Error("Укажите корректную дату и время");
  return String(Math.floor(t / 1000));
}

function modeLabelRu(mode: string): string {
  if (mode === "replay_speed") return "Скорость replay";
  if (mode === "rolling_window") return "Скользящее окно";
  return mode;
}

function formatAsOfUnix(sec: number): string {
  try {
    return new Date(sec * 1000).toLocaleString("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return String(sec);
  }
}

export function ProcessGraphPage() {
  const navigate = useNavigate();
  const [pipelines, setPipelines] = useState<AmoPipelineListItem[]>([]);
  const [pipelinesLoading, setPipelinesLoading] = useState(true);
  const [pipelinesError, setPipelinesError] = useState<string | null>(null);
  const [pipelineId, setPipelineId] = useState("");
  const [asOfLocal, setAsOfLocal] = useState(() => toDatetimeLocalValue(new Date()));
  const [mode, setMode] = useState<"replay_speed" | "rolling_window">("replay_speed");
  const [windowMinutes, setWindowMinutes] = useState("30");
  const [topK, setTopK] = useState("20");
  const [graph, setGraph] = useState<ProcessGraphResponse | null>(null);
  const [coverage, setCoverage] = useState<LeadLinkCoverageResponse | null>(null);
  const [topContacts, setTopContacts] = useState<TopContactsByLeadsResponse | null>(null);
  const [topCompanies, setTopCompanies] = useState<TopCompaniesByLeadsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extrasHint, setExtrasHint] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [analyticsTab, setAnalyticsTab] = useState<"macro" | "micro">("macro");
  const [leadFilter, setLeadFilter] = useState<"activity_in_window" | "open_in_pipeline">(
    "activity_in_window"
  );
  const [microLimit, setMicroLimit] = useState("15");
  const [journeyData, setJourneyData] = useState<LeadJourneysResponse | null>(null);
  const [journeyLoading, setJourneyLoading] = useState(false);
  const [journeyError, setJourneyError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setPipelinesLoading(true);
      setPipelinesError(null);
      try {
        const { pipelines: list } = await getPipelines();
        if (cancelled) return;
        setPipelines(list);
        setPipelineId((prev) => {
          if (prev && list.some((p) => String(p.id) === prev)) return prev;
          return list[0] ? String(list[0].id) : "";
        });
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof ApiError ? err.message : String(err);
        setPipelinesError(msg);
        setPipelineId((prev) => prev || "1");
      } finally {
        if (!cancelled) setPipelinesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedPipelineName =
    pipelines.find((p) => String(p.id) === pipelineId)?.name ?? null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setExtrasHint(null);
    setLoading(true);
    setGraph(null);
    setCoverage(null);
    setTopContacts(null);
    setTopCompanies(null);
    try {
      const pid = Number(pipelineId);
      if (Number.isNaN(pid) || pid <= 0) throw new Error("Выберите воронку или укажите корректный id");
      const w = mode === "rolling_window" ? Number(windowMinutes) : null;
      if (mode === "rolling_window" && (Number.isNaN(w!) || w! <= 0)) {
        throw new Error("Для скользящего окна укажите окно в минутах больше 0");
      }
      const tk = Number(topK);
      if (Number.isNaN(tk) || tk <= 0) throw new Error("Поле top_k должно быть числом больше 0");

      const asOfParam = datetimeLocalToAsOfParam(asOfLocal);

      const graphData = await getProcessGraph({
        pipeline_id: pid,
        as_of: asOfParam,
        mode,
        window_minutes: w ?? undefined,
        top_k: tk,
      });
      setGraph(graphData);

      const settled = await Promise.allSettled([
        getLeadLinkCoverage(pid, false),
        getTopContactsByLeads(pid, tk, false),
        getTopCompaniesByLeads(pid, tk, false),
      ]);

      const [cov, contacts, companies] = settled;
      if (cov.status === "fulfilled") setCoverage(cov.value);
      if (contacts.status === "fulfilled") setTopContacts(contacts.value);
      if (companies.status === "fulfilled") setTopCompanies(companies.value);

      const failed404 = settled.filter(
        (r) => r.status === "rejected" && r.reason instanceof ApiError && r.reason.status === 404
      );
      if (failed404.length > 0) {
        setExtrasHint(
          "Доп. срезы (связи и топы) недоступны на этом backend (часто 404 у старого образа web). Пересоберите: docker compose build web && docker compose up -d web"
        );
      }
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

  async function onSubmitMicro(e: FormEvent) {
    e.preventDefault();
    setJourneyError(null);
    setJourneyLoading(true);
    setJourneyData(null);
    try {
      const pid = Number(pipelineId);
      if (Number.isNaN(pid) || pid <= 0) throw new Error("Выберите воронку или укажите корректный id");
      const wm = Number(windowMinutes);
      if (Number.isNaN(wm) || wm <= 0) throw new Error("Укажите окно в минутах больше 0");
      const lim = Number(microLimit);
      if (Number.isNaN(lim) || lim <= 0) throw new Error("Лимит лидов должен быть числом больше 0");
      const asOfParam = datetimeLocalToAsOfParam(asOfLocal);
      const data = await getLeadJourneys({
        pipeline_id: pid,
        as_of: asOfParam,
        window_minutes: wm,
        lead_filter: leadFilter,
        limit: lim,
      });
      setJourneyData(data);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : String(err);
      setJourneyError(msg);
    } finally {
      setJourneyLoading(false);
    }
  }

  const showTopBlock =
    analyticsTab === "macro" && graph && (topContacts !== null || topCompanies !== null);

  return (
    <div className="mx-auto max-w-6xl p-4">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold text-slate-100">Аналитика воронки</h1>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          Выйти
        </button>
      </header>

      <div className="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setAnalyticsTab("macro")}
          className={`rounded px-4 py-2 text-sm font-medium ${
            analyticsTab === "macro"
              ? "bg-sky-700 text-white"
              : "border border-slate-600 text-slate-300 hover:bg-slate-800"
          }`}
        >
          Макроаналитика
        </button>
        <button
          type="button"
          onClick={() => setAnalyticsTab("micro")}
          className={`rounded px-4 py-2 text-sm font-medium ${
            analyticsTab === "micro"
              ? "bg-emerald-700 text-white"
              : "border border-slate-600 text-slate-300 hover:bg-slate-800"
          }`}
        >
          Микроаналитика
        </button>
      </div>

      {pipelinesError ? (
        <p className="mb-4 rounded border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          Не удалось загрузить список воронок ({pipelinesError}). Укажите id воронки вручную ниже.
        </p>
      ) : null}

      <form
        onSubmit={analyticsTab === "macro" ? onSubmit : onSubmitMicro}
        className="mb-6 grid gap-4 rounded-lg border border-slate-700 bg-slate-900/50 p-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        <label className="text-sm text-slate-300 sm:col-span-2 lg:col-span-1">
          Воронка
          {pipelinesLoading ? (
            <p className="mt-2 text-xs text-slate-500">Загрузка списка…</p>
          ) : pipelinesError ? (
            <input
              type="text"
              inputMode="numeric"
              value={pipelineId}
              onChange={(e) => setPipelineId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              required
              placeholder="id воронки"
            />
          ) : (
            <select
              value={pipelineId}
              onChange={(e) => setPipelineId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              required
              disabled={pipelines.length === 0}
            >
              {pipelines.length === 0 ? (
                <option value="">Нет воронок в базе</option>
              ) : (
                pipelines.map((p) => (
                  <option key={p.id} value={String(p.id)}>
                    {p.name} (id {p.id})
                  </option>
                ))
              )}
            </select>
          )}
        </label>

        <label className="text-sm text-slate-300 sm:col-span-2 lg:col-span-2">
          Дата и время среза
          <input
            type="datetime-local"
            value={asOfLocal}
            onChange={(e) => setAsOfLocal(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
            required
          />
          <span className="mt-1 block text-xs text-slate-500">
            Локальное время браузера; на сервер уходит unix-секунда для расчёта графа.
          </span>
        </label>

        {analyticsTab === "macro" ? (
          <>
            <label className="text-sm text-slate-300">
              Режим расчёта
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as "replay_speed" | "rolling_window")}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              >
                <option value="replay_speed">Скорость replay</option>
                <option value="rolling_window">Скользящее окно</option>
              </select>
            </label>

            <label className="text-sm text-slate-300">
              Окно, минут
              <input
                type="text"
                inputMode="numeric"
                value={windowMinutes}
                onChange={(e) => setWindowMinutes(e.target.value)}
                disabled={mode !== "rolling_window"}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 disabled:opacity-40"
                placeholder="только для скользящего окна"
              />
              <span className="mt-1 block text-xs text-slate-500">
                Используется, если выбран режим «Скользящее окно».
              </span>
            </label>

            <label className="text-sm text-slate-300">
              Лимит рёбер графа и топов (top_k)
              <input
                type="text"
                inputMode="numeric"
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              />
              <span className="mt-1 block text-xs text-slate-500">
                Сколько самых частых переходов показать на графе и сколько строк в топах контактов/компаний.
              </span>
            </label>

            <div className="flex items-end sm:col-span-2 lg:col-span-3">
              <button
                type="submit"
                disabled={loading || pipelinesLoading || (!pipelinesError && pipelines.length === 0)}
                className="w-full rounded bg-sky-600 py-2 font-medium text-white hover:bg-sky-500 disabled:opacity-50 lg:max-w-xs"
              >
                {loading ? "Загрузка…" : "Загрузить граф"}
              </button>
            </div>
          </>
        ) : (
          <>
            <label className="text-sm text-slate-300">
              Окно, минут (t)
              <input
                type="text"
                inputMode="numeric"
                value={windowMinutes}
                onChange={(e) => setWindowMinutes(e.target.value)}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
                required
              />
              <span className="mt-1 block text-xs text-slate-500">
                Интервал [срез − t, срез]; переходы внутри него подсвечиваются зелёным.
              </span>
            </label>

            <label className="text-sm text-slate-300">
              Отбор лидов
              <select
                value={leadFilter}
                onChange={(e) =>
                  setLeadFilter(e.target.value as "activity_in_window" | "open_in_pipeline")
                }
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              >
                <option value="activity_in_window">Был переход в окне</option>
                <option value="open_in_pipeline">Открытая сделка (текущий статус не финал)</option>
              </select>
              <span className="mt-1 block text-xs text-slate-500">
                «Открытая» — по текущему статусу в БД, не по историческому срезу.
              </span>
            </label>

            <label className="text-sm text-slate-300">
              Сколько лидов (k)
              <input
                type="text"
                inputMode="numeric"
                value={microLimit}
                onChange={(e) => setMicroLimit(e.target.value)}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5"
              />
            </label>

            <div className="flex flex-col justify-end sm:col-span-2 lg:col-span-3">
              <p className="mb-2 text-xs text-slate-500">
                Для каждого лида — цепочка статусов до среза; зелёным выделены переходы, попавшие в окно.
              </p>
              <button
                type="submit"
                disabled={journeyLoading || pipelinesLoading || (!pipelinesError && pipelines.length === 0)}
                className="w-full rounded bg-emerald-700 py-2 font-medium text-white hover:bg-emerald-600 disabled:opacity-50 lg:max-w-xs"
              >
                {journeyLoading ? "Загрузка…" : "Загрузить микро"}
              </button>
            </div>
          </>
        )}
      </form>

      {analyticsTab === "macro" && error ? (
        <p className="mb-4 rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      ) : null}

      {analyticsTab === "micro" && journeyError ? (
        <p className="mb-4 rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {journeyError}
        </p>
      ) : null}

      {analyticsTab === "macro" && extrasHint ? (
        <p className="mb-4 rounded border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {extrasHint}
        </p>
      ) : null}

      {analyticsTab === "macro" && graph ? (
        <section className="mb-4 rounded-lg border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Параметры среза</h2>
          <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-slate-500">Воронка</dt>
              <dd className="font-medium text-slate-100">
                {selectedPipelineName ?? "—"}
                <span className="text-slate-500"> · id {graph.meta.pipeline_id}</span>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Момент среза (как на сервере)</dt>
              <dd className="font-medium text-slate-100">{formatAsOfUnix(graph.meta.as_of)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Режим</dt>
              <dd className="font-medium text-slate-100">{modeLabelRu(graph.meta.mode)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Окно, минут</dt>
              <dd className="font-medium text-slate-100">
                {graph.meta.window_minutes != null ? `${graph.meta.window_minutes}` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Лимит top_k (рёбра + топы)</dt>
              <dd className="font-medium text-slate-100">{graph.meta.top_k}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      {analyticsTab === "macro" && coverage ? (
        <section className="mb-6 grid gap-3 rounded-lg border border-slate-700 bg-slate-900/50 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded border border-slate-700 bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">Всего лидов в воронке</p>
            <p className="text-xl font-semibold text-slate-100">{coverage.coverage.total_leads}</p>
          </div>
          <div className="rounded border border-slate-700 bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">С контактами</p>
            <p className="text-xl font-semibold text-slate-100">
              {coverage.coverage.with_contacts} ({(coverage.coverage.contact_ratio * 100).toFixed(1)}%)
            </p>
            {coverage.coverage.contact_ratio === 0 && coverage.coverage.total_leads > 0 ? (
              <p className="mt-2 text-xs text-slate-500">
                Нет связей в bridge-таблице или не выполнен materialize_amo_bridges.
              </p>
            ) : null}
          </div>
          <div className="rounded border border-slate-700 bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">С компаниями</p>
            <p className="text-xl font-semibold text-slate-100">
              {coverage.coverage.with_companies} ({(coverage.coverage.company_ratio * 100).toFixed(1)}%)
            </p>
            {coverage.coverage.company_ratio === 0 && coverage.coverage.total_leads > 0 ? (
              <p className="mt-2 text-xs text-slate-500">
                Нет связей в bridge-таблице или не выполнен materialize_amo_bridges.
              </p>
            ) : null}
          </div>
          <div className="rounded border border-slate-700 bg-slate-950/70 p-3">
            <p className="text-xs text-slate-400">Воронка</p>
            <p className="text-xl font-semibold text-slate-100">
              {selectedPipelineName ?? `id ${coverage.pipeline_id}`}
            </p>
          </div>
        </section>
      ) : null}

      {showTopBlock ? (
        <section className="mb-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-200">Топ контактов по числу лидов</h2>
            {topContacts ? (
              topContacts.contacts.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Нет данных: у лидов этой воронки нет связанных контактов в материализованных связях.
                </p>
              ) : (
                <div className="max-h-52 overflow-auto">
                  <table className="w-full text-sm text-slate-200">
                    <thead className="text-xs text-slate-400">
                      <tr>
                        <th className="py-1 text-left">ID контакта</th>
                        <th className="py-1 text-right">Лидов</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topContacts.contacts.map((x) => (
                        <tr key={x.contact_id} className="border-t border-slate-800">
                          <td className="py-1">{x.contact_id}</td>
                          <td className="py-1 text-right">{x.leads_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              <p className="text-sm text-slate-500">Срез не загружен.</p>
            )}
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-200">Топ компаний по числу лидов</h2>
            {topCompanies ? (
              topCompanies.companies.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Нет данных: у лидов этой воронки нет связанных компаний в материализованных связях.
                </p>
              ) : (
                <div className="max-h-52 overflow-auto">
                  <table className="w-full text-sm text-slate-200">
                    <thead className="text-xs text-slate-400">
                      <tr>
                        <th className="py-1 text-left">ID компании</th>
                        <th className="py-1 text-right">Лидов</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topCompanies.companies.map((x) => (
                        <tr key={x.company_id} className="border-t border-slate-800">
                          <td className="py-1">{x.company_id}</td>
                          <td className="py-1 text-right">{x.leads_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              <p className="text-sm text-slate-500">Срез не загружен.</p>
            )}
          </div>
        </section>
      ) : null}

      {analyticsTab === "macro" ? (
        <section className="mb-2">
          <h2 className="mb-2 text-sm font-semibold text-slate-300">Граф переходов (макро)</h2>
          <ProcessGraphFlow data={graph} />
        </section>
      ) : null}

      {analyticsTab === "micro" && journeyData ? (
        <section className="mb-6 space-y-4">
          <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 text-sm text-slate-300">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Срез микро</h2>
            <p className="text-xs text-slate-400">
              Окно: {formatAsOfUnix(journeyData.meta.window_start_ts)} —{" "}
              {formatAsOfUnix(journeyData.meta.window_end_ts)} · {journeyData.meta.window_minutes} мин · отбор:{" "}
              {journeyData.meta.lead_filter}
            </p>
            {journeyData.meta.open_leads_note ? (
              <p className="mt-2 text-xs text-amber-200/90">{journeyData.meta.open_leads_note}</p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-4 text-xs">
              <span>
                <span className="inline-block h-3 w-3 rounded border border-slate-500 bg-slate-700 align-middle" />{" "}
                вне окна / история
              </span>
              <span>
                <span className="inline-block h-3 w-3 rounded border border-emerald-500 bg-emerald-900/50 align-middle" />{" "}
                переход в окне
              </span>
            </div>
          </div>

          {journeyData.leads.map((lead) => (
            <div
              key={lead.lead_id}
              className="rounded-lg border border-slate-700 bg-slate-900/40 p-4"
            >
              <h3 className="mb-2 text-sm font-semibold text-slate-200">
                Лид {lead.lead_id}
                {lead.name ? ` · ${lead.name}` : ""}
              </h3>
              <LeadJourneyChain
                lead={lead}
                statuses={journeyData.statuses}
                pipelineId={journeyData.meta.pipeline_id}
              />
            </div>
          ))}
        </section>
      ) : null}
    </div>
  );
}
