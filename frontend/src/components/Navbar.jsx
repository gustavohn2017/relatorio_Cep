/**
 * Navbar.jsx — Barra de navegação superior.
 *
 * Exibe logo, links e estado de autenticação.
 * Responsivo — menu hambúrguer em telas pequenas.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { HiMenu, HiX } from "react-icons/hi";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
    setOpen(false);
  };

  return (
    <nav className="bg-white border-b border-brand-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="text-lg font-bold text-brand-800 tracking-tight">
            Relatório<span className="text-brand-500">CEP</span>
          </Link>

          {/* Links desktop */}
          <div className="hidden md:flex items-center gap-6 text-sm">
            <Link to="/" className="text-brand-600 hover:text-brand-900 transition">
              Análise
            </Link>
            {user && (
              <Link to="/history" className="text-brand-600 hover:text-brand-900 transition">
                Histórico
              </Link>
            )}
            {user ? (
              <div className="flex items-center gap-4">
                <span className="text-brand-400">Olá, {user.username}</span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1.5 text-sm bg-brand-800 text-white rounded hover:bg-brand-700 transition"
                >
                  Sair
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="px-3 py-1.5 text-sm border border-brand-300 rounded hover:bg-brand-100 transition"
                >
                  Entrar
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1.5 text-sm bg-brand-800 text-white rounded hover:bg-brand-700 transition"
                >
                  Cadastrar
                </Link>
              </div>
            )}
          </div>

          {/* Hambúrguer mobile */}
          <button
            onClick={() => setOpen(!open)}
            className="md:hidden text-brand-600 hover:text-brand-900"
          >
            {open ? <HiX size={24} /> : <HiMenu size={24} />}
          </button>
        </div>
      </div>

      {/* Menu mobile */}
      {open && (
        <div className="md:hidden border-t border-brand-200 bg-white px-4 pb-4 space-y-2">
          <Link
            to="/"
            onClick={() => setOpen(false)}
            className="block py-2 text-brand-600 hover:text-brand-900"
          >
            Análise
          </Link>
          {user && (
            <Link
              to="/history"
              onClick={() => setOpen(false)}
              className="block py-2 text-brand-600 hover:text-brand-900"
            >
              Histórico
            </Link>
          )}
          {user ? (
            <button
              onClick={handleLogout}
              className="w-full text-left py-2 text-red-600 hover:text-red-800"
            >
              Sair ({user.username})
            </button>
          ) : (
            <>
              <Link
                to="/login"
                onClick={() => setOpen(false)}
                className="block py-2 text-brand-600 hover:text-brand-900"
              >
                Entrar
              </Link>
              <Link
                to="/register"
                onClick={() => setOpen(false)}
                className="block py-2 text-brand-600 hover:text-brand-900"
              >
                Cadastrar
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
