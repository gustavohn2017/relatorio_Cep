/**
 * LoginPage.jsx — Tela de login.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === "object" && data.detail) {
        setError(data.detail);
      } else if (typeof data === "string" && data.includes("<html")) {
        setError("Erro no servidor. Tente novamente mais tarde.");
      } else {
        setError("Credenciais inválidas. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-full max-w-sm bg-white rounded-xl border border-brand-200 p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-bold text-brand-900">Entrar</h1>
          <p className="text-sm text-brand-400 mt-1">
            Acesse sua conta para ver seu histórico
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-brand-700 mb-1">
              Usuário
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-brand-700 mb-1">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-brand-800 text-white rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 transition"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <div className="text-center space-y-2">
          <Link
            to="/password-reset"
            className="text-sm text-brand-500 hover:text-brand-700 underline"
          >
            Esqueceu a senha?
          </Link>
          <p className="text-sm text-brand-400">
            Não tem conta?{" "}
            <Link
              to="/register"
              className="text-brand-700 font-medium hover:underline"
            >
              Cadastre-se
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
