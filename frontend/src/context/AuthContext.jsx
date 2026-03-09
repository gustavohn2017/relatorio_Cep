/**
 * AuthContext.jsx — Context global de autenticação.
 *
 * Gerencia login (tradicional + social), logout, registro e dados do usuário.
 * Armazena tokens JWT no localStorage.
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import api from "../api";

const AuthContext = createContext(null);

// URLs OAuth (construídas com variáveis de ambiente)
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const MICROSOFT_CLIENT_ID = import.meta.env.VITE_MICROSOFT_CLIENT_ID || "";

export function getGoogleAuthUrl() {
  const redirectUri = encodeURIComponent(window.location.origin + "/auth/callback");
  const scope = encodeURIComponent(
    "openid email profile https://www.googleapis.com/auth/spreadsheets.readonly"
  );
  return (
    `https://accounts.google.com/o/oauth2/v2/auth` +
    `?client_id=${GOOGLE_CLIENT_ID}` +
    `&redirect_uri=${redirectUri}` +
    `&response_type=code` +
    `&scope=${scope}` +
    `&access_type=offline` +
    `&prompt=consent` +
    `&state=google`
  );
}

export function getMicrosoftAuthUrl() {
  const redirectUri = encodeURIComponent(window.location.origin + "/auth/callback");
  const scope = encodeURIComponent("openid email profile User.Read");
  return (
    `https://login.microsoftonline.com/common/oauth2/v2.0/authorize` +
    `?client_id=${MICROSOFT_CLIENT_ID}` +
    `&redirect_uri=${redirectUri}` +
    `&response_type=code` +
    `&scope=${scope}` +
    `&response_mode=query` +
    `&state=microsoft`
  );
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Carrega dados do usuário ao montar (se houver token)
  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me/");
      setUser(data.user);
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Login tradicional
  const login = async (username, password) => {
    const { data } = await api.post("/auth/token/", { username, password });
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    await fetchUser();
  };

  // Login social — troca authorization code por JWT
  const socialLogin = async (provider, code) => {
    const redirectUri = window.location.origin + "/auth/callback";
    const { data } = await api.post(`/auth/social/${provider}/`, {
      code,
      redirect_uri: redirectUri,
    });
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    await fetchUser();
  };

  // Registro tradicional
  const register = async (username, email, password, passwordConfirm) => {
    await api.post("/auth/register/", {
      username,
      email,
      password,
      password_confirm: passwordConfirm,
    });
    await login(username, password);
  };

  // Logout
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, socialLogin, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
