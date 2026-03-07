/**
 * PasswordResetConfirmPage.jsx — Definir nova senha via link recebido por e-mail.
 */

import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api";

export default function PasswordResetConfirmPage() {
  const { uid, token } = useParams();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/password-reset-confirm/", {
        uid,
        token,
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Erro ao redefinir senha. O link pode ter expirado."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-full max-w-sm bg-white rounded-xl border border-brand-200 p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-bold text-brand-900">
            Nova Senha
          </h1>
        </div>

        {success ? (
          <div className="text-center space-y-4">
            <div className="text-green-600 bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
              Senha redefinida com sucesso!
            </div>
            <Link
              to="/login"
              className="inline-block px-4 py-2 bg-brand-800 text-white rounded-lg text-sm hover:bg-brand-700 transition"
            >
              Ir para login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-brand-700 mb-1">
                Nova senha
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-700 mb-1">
                Confirmar nova senha
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
              {loading ? "Redefinindo..." : "Redefinir senha"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
