import React, { useState } from "react";
import api from "../api/axios.js";
import { useLiveData } from "../hooks/useSocket.js";
import { TrafficTable } from "../components/Tables.jsx";

export default function Traffic() {
  const [blockedOnly, setBlockedOnly] = useState(false);

  const { data, loading, refetch } = useLiveData(
    () => api.get(`/traffic?limit=50&blocked_only=${blockedOnly}`).then((r) => r.data),
    6000,
    [blockedOnly]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">Live Traffic</h1>
        <label className="flex items-center gap-2 text-sm text-slate-400">
          <input
            type="checkbox"
            checked={blockedOnly}
            onChange={(e) => setBlockedOnly(e.target.checked)}
            className="accent-sky-500"
          />
          Blocked only
        </label>
      </div>

      {loading && !data ? (
        <p className="text-slate-500">Loading...</p>
      ) : (
        <TrafficTable rows={data?.items || []} />
      )}

      <p className="text-xs text-slate-600">Total matching: {data?.total ?? 0} · auto-refreshes every 6s</p>
    </div>
  );
}
