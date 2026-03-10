/**
 * RegisterPage.jsx — Tela de cadastro de novo usuário (tradicional + social).
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, getGoogleAuthUrl } from "../context/AuthContext";
import { FcGoogle } from "react-icons/fc";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("As senhas não coincidem.");
      return;
    }

    setLoading(true);
    try {
      await register(username, email, password, passwordConfirm);
      navigate("/");
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === "object" && !Array.isArray(data)) {
        const msgs = Object.entries(data)
          .map(([key, val]) => {
            const label = key === "detail" ? "" : `${key}: `;
            const msg = Array.isArray(val) ? val.join(", ") : String(val);
            return `${label}${msg}`;
          })
          .join(" | ");
        setError(msgs);
      } else if (typeof data === "string" && data.includes("<html")) {
        setError("Erro no servidor. Por favor, tente novamente mais tarde.");
      } else {
        setError("Erro ao cadastrar. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-full max-w-sm bg-white rounded-xl border border-brand-200 p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-bold text-brand-900">Criar Conta</h1>
          <p className="text-sm text-brand-400 mt-1">
            Cadastre-se para salvar seu histórico de análises
          </p>
        </div>

        {/* Botões de cadastro social */}
        <div className="space-y-3">
          <a
            href={getGoogleAuthUrl()}
            className="w-full flex items-center justify-center gap-3 py-2.5 border border-brand-300 rounded-lg text-sm font-medium text-brand-700 hover:bg-brand-50 transition"
          >
            <FcGoogle size={20} />
            Cadastrar com Google
          </a>
        </div>

        {/* Separador */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-brand-200" />
          <span className="text-xs text-brand-400">ou</span>
          <div className="flex-1 h-px bg-brand-200" />
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
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
              minLength={8}
              className="w-full px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-brand-700 mb-1">
              Confirmar Senha
            </label>
            <input
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-brand-800 text-white rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 transition"
          >
            {loading ? "Cadastrando..." : "Cadastrar"}
          </button>
        </form>

        <p className="text-center text-sm text-brand-400">
          Já tem conta?{" "}
          <Link
            to="/login"
            className="text-brand-700 font-medium hover:underline"
          >
            Entrar
          </Link>
        </p>
      </div>
    </div>
  );
}
