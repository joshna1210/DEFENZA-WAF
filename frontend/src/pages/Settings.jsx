import React, { useState } from "react";
import api from "../api/axios.js";

export default function Settings() {
  const [payload, setPayload] = useState({
    method: "GET",
    path: "/login",
    query_string: "id=1' OR '1'='1",
    body: "",
  });
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  const runTest = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/analysis/test", payload);
      setResult(data);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-lg font-semibold text-slate-100">Settings & rule tester</h1>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Test the analysis pipeline</h2>
        <p className="text-xs text-slate-500">
          Run any payload through the rule + keyword + (optional) ML engine without needing live
          proxy traffic. Useful when tuning rules in <code>backend/app/services/rule_engine.py</code>.
        </p>

        <div className="grid grid-cols-2 gap-3">
          <input
            className="bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100"
            placeholder="Method"
            value={payload.method}
            onChange={(e) => setPayload({ ...payload, method: e.target.value })}
          />
          <input
            className="bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100"
            placeholder="Path"
            value={payload.path}
            onChange={(e) => setPayload({ ...payload, path: e.target.value })}
          />
        </div>
        <input
          className="w-full bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100"
          placeholder="Query string"
          value={payload.query_string}
          onChange={(e) => setPayload({ ...payload, query_string: e.target.value })}
        />
        <textarea
          className="w-full bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100"
          placeholder="Body"
          rows={3}
          value={payload.body}
          onChange={(e) => setPayload({ ...payload, body: e.target.value })}
        />

        <button
          onClick={runTest}
          disabled={running}
          className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-md"
        >
          {running ? "Analyzing..." : "Analyze payload"}
        </button>

        {result && (
          <pre className="bg-slate-950 border border-slate-800 rounded-md p-3 text-xs text-slate-300 overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
