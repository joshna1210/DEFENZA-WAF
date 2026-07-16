import React, { createContext, useContext, useState, useEffect } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("waf_token"));
  const [role, setRole] = useState(() => localStorage.getItem("waf_role"));

  useEffect(() => {
    if (token) localStorage.setItem("waf_token", token);
    else localStorage.removeItem("waf_token");
  }, [token]);

  useEffect(() => {
    if (role) localStorage.setItem("waf_role", role);
    else localStorage.removeItem("waf_role");
  }, [role]);

  const login = (newToken, newRole) => {
    setToken(newToken);
    setRole(newRole);
  };

  const logout = () => {
    setToken(null);
    setRole(null);
  };

  return (
    <AppContext.Provider value={{ token, role, login, logout, isAuthenticated: !!token }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
