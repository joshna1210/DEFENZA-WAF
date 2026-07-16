import React from "react";
import api from "../api/axios.js";
import { useLiveData } from "../hooks/useSocket.js";
import { RequestsOverTimeChart, CategoryBreakdownChart } from "../components/Charts.jsx";

function StatCard({ label, value, tone = "default" }) {
  const toneClass = {
    default: "text-slate-100",
    danger: "text-risk-critical",
    warn: "text-risk-high",
  }[tone];
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${toneClass}`}>{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const { data: summary, loading } = useLiveData(
    () => api.get("/reports/summary?hours=24").then((r) => r.data),
    8000
  );
  const { data: alerts } = useLiveData(
    () => api.get("/alerts?limit=10").then((r) => r.data),
    8000
  );

  if (loading && !summary) {
    return <p className="text-slate-500">Loading dashboard...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Requests (24h)" value={summary?.total_requests ?? 0} />
        <StatCard label="Blocked" value={summary?.blocked_requests ?? 0} tone="danger" />
        <StatCard label="High Risk" value={summary?.high_risk_requests ?? 0} tone="warn" />
        <StatCard label="Unique IPs" value={summary?.unique_ips ?? 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h2 className="text-sm font-medium text-slate-300 mb-2">Requests over time</h2>
          <RequestsOverTimeChart data={summary?.requests_over_time || []} />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h2 className="text-sm font-medium text-slate-300 mb-2">Attack category breakdown</h2>
          <CategoryBreakdownChart data={summary?.top_categories || {}} />
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Recent alerts</h2>
        <ul className="space-y-2">
          {(alerts || []).map((a) => (
            <li key={a.id} className="flex items-center justify-between text-sm border-b border-slate-800 pb-2 last:border-0">
              <span className="text-slate-300">
                <span className="font-mono text-slate-400">{a.ip}</span> — {a.category}
              </span>
              <span className="text-risk-high font-medium">{a.risk_score}</span>
            </li>
          ))}
          {(!alerts || alerts.length === 0) && (
            <p className="text-slate-500 text-sm">No active alerts. Nice and quiet.</p>
          )}
        </ul>
      </div>
    </div>
  );
}
