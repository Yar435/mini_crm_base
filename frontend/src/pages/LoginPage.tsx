import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { ApiError, isAuthenticated } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate("/", { replace: true });
    }
  }, [navigate]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Не удалось войти";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 rounded-xl border border-slate-700 bg-slate-900/80 p-6 shadow-xl"
      >
        <h1 className="text-center text-xl font-semibold text-slate-100">Вход</h1>
        <p className="text-center text-sm text-slate-400">Учётные данные Django (JWT)</p>
        {error ? (
          <p className="rounded border border-red-900/60 bg-red-950/50 px-3 py-2 text-sm text-red-200">
            {error}
          </p>
        ) : null}
        <label className="block text-sm text-slate-300">
          Имя пользователя
          <input
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-500"
            required
          />
        </label>
        <label className="block text-sm text-slate-300">
          Пароль
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-500"
            required
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-sky-600 py-2 font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? "Вход…" : "Войти"}
        </button>
      </form>
    </div>
  );
}
