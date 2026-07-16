import React from "react";
import { useApp } from "../context/AppContext.jsx";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { role, logout } = useApp();
  const navigate = useNavigate();

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-900 flex items-center justify-between px-6">
      <div className="font-semibold tracking-tight text-slate-100">
        AI-WAF <span className="text-slate-500 font-normal">/ blockchain-audited</span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {role && <span className="px-2 py-1 rounded bg-slate-800 text-slate-300">{role}</span>}
        <button
          onClick={() => {
            logout();
            navigate("/login");
          }}
          className="text-slate-400 hover:text-slate-100"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
