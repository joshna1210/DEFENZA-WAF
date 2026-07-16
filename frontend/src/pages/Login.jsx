import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios.js";
import { useApp } from "../context/AppContext.jsx";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("soc_analyst");
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [error, setError] = useState("");
  const { login } = useApp();
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const payload = mode === "login" ? { username, password } : { username, password, role };
      const { data } = await api.post(endpoint, payload);
      login(data.access_token, data.role);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <form onSubmit={submit} className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h1 className="text-lg font-semibold text-slate-100">
          {mode === "login" ? "Sign in to AI-WAF" : "Create an account"}
        </h1>

        <input
          className="w-full bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-sky-500"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          className="w-full bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-sky-500"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {mode === "register" && (
          <select
            className="w-full bg-slate-800 rounded-md px-3 py-2 text-sm text-slate-100"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="soc_analyst">SOC Analyst</option>
            <option value="admin">Admin</option>
          </select>
        )}

        {error && <p className="text-sm text-risk-critical">{error}</p>}

        <button type="submit" className="w-full bg-sky-600 hover:bg-sky-500 text-white rounded-md py-2 text-sm font-medium">
          {mode === "login" ? "Sign in" : "Register"}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="w-full text-xs text-slate-400 hover:text-slate-200"
        >
          {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
