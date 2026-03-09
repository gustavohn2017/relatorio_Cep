/**
 * OAuthCallbackPage.jsx — Página de callback para login social.
 *
 * Captura o authorization code retornado pelo provedor OAuth
 * (Google ou Microsoft), envia ao backend para troca por JWT
 * e redireciona o usuário para a home.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { socialLogin } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state"); // "google" ou "microsoft"
    const oauthError = params.get("error");

    if (oauthError) {
      setError("Autenticação cancelada ou negada pelo provedor.");
      return;
    }

    if (!code || !state) {
      setError("Parâmetros de autenticação inválidos.");
      return;
    }

    let cancelled = false;

    const doLogin = async () => {
      try {
        await socialLogin(state, code);
        if (!cancelled) navigate("/");
      } catch (err) {
        if (!cancelled) {
          const detail = err.response?.data?.detail;
          setError(detail || "Erro ao autenticar. Tente novamente.");
        }
      }
    };

    doLogin();

    return () => {
      cancelled = true;
    };
  }, [params, navigate, socialLogin]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <p className="text-red-600">{error}</p>
          <Link
            to="/login"
            className="text-brand-700 font-medium hover:underline"
          >
            Voltar ao login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-2">
        <div className="animate-spin h-8 w-8 border-4 border-brand-300 border-t-brand-700 rounded-full mx-auto" />
        <p className="text-brand-600 text-sm">Autenticando...</p>
      </div>
    </div>
  );
}
