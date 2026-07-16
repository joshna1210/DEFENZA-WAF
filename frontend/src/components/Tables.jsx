import React from "react";

const RISK_COLORS = {
  low: "bg-risk-low/20 text-risk-low",
  medium: "bg-risk-medium/20 text-risk-medium",
  high: "bg-risk-high/20 text-risk-high",
  critical: "bg-risk-critical/20 text-risk-critical",
};

export function RiskBadge({ level }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_COLORS[level] || "bg-slate-700 text-slate-300"}`}>
      {level}
    </span>
  );
}

export function TrafficTable({ rows }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Time</th>
            <th className="text-left px-4 py-2 font-medium">IP</th>
            <th className="text-left px-4 py-2 font-medium">Method</th>
            <th className="text-left px-4 py-2 font-medium">Path</th>
            <th className="text-left px-4 py-2 font-medium">Status</th>
            <th className="text-left px-4 py-2 font-medium">Risk</th>
            <th className="text-left px-4 py-2 font-medium">Blocked</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((row) => (
            <tr key={row.id} className="hover:bg-slate-900/50">
              <td className="px-4 py-2 text-slate-400 whitespace-nowrap">
                {new Date(row.timestamp).toLocaleTimeString()}
              </td>
              <td className="px-4 py-2 font-mono text-slate-300">{row.ip}</td>
              <td className="px-4 py-2 text-slate-300">{row.method}</td>
              <td className="px-4 py-2 text-slate-300 truncate max-w-xs">{row.path}</td>
              <td className="px-4 py-2 text-slate-400">{row.status_code ?? "-"}</td>
              <td className="px-4 py-2">
                <RiskBadge level={row.risk_level} />
              </td>
              <td className="px-4 py-2">
                {row.blocked ? (
                  <span className="text-risk-critical text-xs font-medium">BLOCKED</span>
                ) : (
                  <span className="text-slate-500 text-xs">allowed</span>
                )}
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                No traffic yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function IpTable({ rows }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="text-left px-4 py-2 font-medium">IP</th>
            <th className="text-left px-4 py-2 font-medium">Requests</th>
            <th className="text-left px-4 py-2 font-medium">Blocked</th>
            <th className="text-left px-4 py-2 font-medium">Avg Risk</th>
            <th className="text-left px-4 py-2 font-medium">Last Seen</th>
            <th className="text-left px-4 py-2 font-medium">Flagged</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((row) => (
            <tr key={row.ip} className="hover:bg-slate-900/50">
              <td className="px-4 py-2 font-mono text-slate-300">{row.ip}</td>
              <td className="px-4 py-2 text-slate-300">{row.request_count}</td>
              <td className="px-4 py-2 text-slate-300">{row.blocked_count}</td>
              <td className="px-4 py-2 text-slate-300">{row.avg_risk_score}</td>
              <td className="px-4 py-2 text-slate-400">{new Date(row.last_seen).toLocaleString()}</td>
              <td className="px-4 py-2">
                {row.flagged ? (
                  <span className="text-risk-high text-xs font-medium">FLAGGED</span>
                ) : (
                  <span className="text-slate-500 text-xs">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
