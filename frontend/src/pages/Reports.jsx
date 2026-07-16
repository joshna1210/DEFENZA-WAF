import React from "react";
import api from "../api/axios.js";
import { useLiveData } from "../hooks/useSocket.js";
import { IpTable } from "../components/Tables.jsx";
import { CategoryBreakdownChart } from "../components/Charts.jsx";

export default function Reports() {
  const { data: summary } = useLiveData(
    () => api.get("/reports/summary?hours=24").then((r) => r.data),
    10000
  );
  const { data: ips } = useLiveData(
    () => api.get("/reports/ips?limit=50").then((r) => r.data),
    10000
  );
  const { data: batches } = useLiveData(
    () => api.get("/blockchain/batches?limit=10").then((r) => r.data),
    10000
  );

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-100">Reports</h1>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-medium text-slate-300 mb-2">Attack categories (24h)</h2>
        <CategoryBreakdownChart data={summary?.top_categories || {}} />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-medium text-slate-300 mb-3">IP activity</h2>
        <IpTable rows={ips || []} />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Blockchain audit batches</h2>
        <div className="space-y-2">
          {(batches || []).map((b) => (
            <div key={b.id} className="flex items-center justify-between text-sm border-b border-slate-800 pb-2 last:border-0">
              <span className="font-mono text-slate-400 truncate max-w-md">{b.merkle_root}</span>
              <span className="text-slate-300">{b.log_count} logs</span>
              <span className={b.on_chain ? "text-risk-low text-xs" : "text-slate-500 text-xs"}>
                {b.on_chain ? "on-chain" : "local (mock)"}
              </span>
            </div>
          ))}
          {(!batches || batches.length === 0) && (
            <p className="text-slate-500 text-sm">No batches yet — they run automatically every few minutes.</p>
          )}
        </div>
      </div>
    </div>
  );
}
