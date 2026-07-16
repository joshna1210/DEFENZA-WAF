import React from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/traffic", label: "Traffic" },
  { to: "/reports", label: "Reports" },
  { to: "/vulnerability", label: "Vulnerability" },
  { to: "/settings", label: "Settings" },
];

export default function Sidebar() {
  return (
    <nav className="w-56 shrink-0 border-r border-slate-800 bg-slate-900 p-4 space-y-1">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          className={({ isActive }) =>
            `block px-3 py-2 rounded-md text-sm transition-colors ${
              isActive
                ? "bg-slate-800 text-white"
                : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
            }`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
