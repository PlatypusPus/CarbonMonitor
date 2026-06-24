import { createContext, useContext, useEffect, useState } from "react";

import client, { setAccessToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
    setUser(me.data);
  }

  async function logout() {
    try {
      await client.post("/auth/logout");
    } catch {
      // ignore: clearing local state below is what matters
    }
    setAccessToken(null);
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
