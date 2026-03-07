/**
 * PasswordResetPage.jsx — Solicitar link de recuperação de senha.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

export default function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/password-reset/", { email });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Erro ao enviar e-mail.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-full max-w-sm bg-white rounded-xl border border-brand-200 p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-bold text-brand-900">
            Recuperar Senha
          </h1>
          <p className="text-sm text-brand-400 mt-1">
            Informe seu e-mail e enviaremos um link para redefinir sua senha
          </p>
        </div>

        {sent ? (
          <div className="text-center space-y-4">
            <div className="text-green-600 bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
              Se o e-mail estiver cadastrado, um link de recuperação foi enviado.
              Verifique sua caixa de entrada.
            </div>
            <Link
              to="/login"
              className="text-sm text-brand-700 font-medium hover:underline"
            >
              Voltar ao login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
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

            {error && <p className="text-red-600 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-brand-800 text-white rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 transition"
            >
              {loading ? "Enviando..." : "Enviar link de recuperação"}
            </button>

            <p className="text-center text-sm">
              <Link
                to="/login"
                className="text-brand-500 hover:text-brand-700 underline"
              >
                Voltar ao login
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
