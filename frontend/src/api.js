/**
 * api.js — Instância Axios configurada para comunicação com o backend Django.
 *
 * Intercepta requisições para injetar o token JWT automaticamente
 * e tenta renovar o token quando expira.
 */

import axios from "axios";

// Em produção, VITE_API_URL aponta para o backend no Render.
// Em dev, o Vite proxy redireciona /api para localhost:8000.
const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Interceptor de request: injeta token de acesso
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de response: tenta renovar token 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem("refresh_token");

      if (refresh) {
        try {
          const { data } = await axios.post("/api/auth/token/refresh/", {
            refresh,
          });
          localStorage.setItem("access_token", data.access);
          if (data.refresh) {
            localStorage.setItem("refresh_token", data.refresh);
          }
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          // Refresh falhou — limpa tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
