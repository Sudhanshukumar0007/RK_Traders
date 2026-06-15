interface HealthResponse {
  status: string;
  api: string;
  db: string;
}

async function getHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/health`,
      { cache: "no-store" }
    );
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getHealth();

  const statusColor = (val: string | undefined) => {
    if (!val) return "text-red-500";
    if (val === "ok" || val === "connected") return "text-green-500";
    if (val === "degraded") return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 font-sans p-8">
      <div className="w-full max-w-lg rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm p-10 space-y-8">
        {/* Header */}
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Phase 0 — Scaffolding
          </p>
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            Supreme Hardware Store
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Stack health check — confirms frontend → backend → database are all connected.
          </p>
        </div>

        {/* Health Status */}
        <div className="rounded-xl border border-zinc-100 dark:border-zinc-800 divide-y divide-zinc-100 dark:divide-zinc-800 overflow-hidden">
          {[
            { label: "Frontend", value: "ok", note: "Next.js 14 · App Router" },
            { label: "Backend API", value: health?.api, note: "FastAPI · localhost:8000" },
            { label: "Database", value: health?.db, note: "PostgreSQL 16 · docker-compose" },
          ].map(({ label, value, note }) => (
            <div
              key={label}
              className="flex items-center justify-between px-5 py-4 bg-white dark:bg-zinc-900"
            >
              <div>
                <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">{label}</p>
                <p className="text-xs text-zinc-400">{note}</p>
              </div>
              <span className={`text-sm font-mono font-semibold ${statusColor(value)}`}>
                {value ?? "unreachable"}
              </span>
            </div>
          ))}
        </div>

        {/* Raw response */}
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Raw /health response
          </p>
          <pre className="rounded-lg bg-zinc-950 text-green-400 text-xs p-4 overflow-x-auto">
            {health ? JSON.stringify(health, null, 2) : "// Backend unreachable — is uvicorn running on :8000?"}
          </pre>
        </div>

        {/* Next steps */}
        <p className="text-xs text-zinc-400 border-t border-zinc-100 dark:border-zinc-800 pt-6">
          Next: <span className="text-zinc-600 dark:text-zinc-300 font-medium">Phase 1 — Database schema, product catalog models &amp; seed data</span>
        </p>
      </div>
    </div>
  );
}
