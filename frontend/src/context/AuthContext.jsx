import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import client, { setAccessToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const attemptedRefresh = useRef(false);

  useEffect(() => {
    if (attemptedRefresh.current) return;
    attemptedRefresh.current = true;

    if (["/", "/login"].includes(window.location.pathname)) {
      setLoading(false);
      return;
    }

    (async () => {
      try {
        const { data } = await client.post("/auth/refresh");
        setAccessToken(data.access_token);
        const me = await client.get("/auth/me");
        setUser(me.data);
      } catch {
        setAccessToken(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function login(email, password) {
    const { data } = await client.post("/auth/login", { email, password });
    setAccessToken(data.access_token);
    const me = await client.get("/auth/me");
    queryClient.clear();
    setUser(me.data);
    return me.data;
  }

  async function logout() {
    try {
      await client.post("/auth/logout");
    } catch {
      // ignore: clearing local state below is what matters
    }
    setAccessToken(null);
    queryClient.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
