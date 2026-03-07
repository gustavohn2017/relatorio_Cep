/**
 * Layout.jsx — Shell da aplicação com Navbar e footer.
 */

import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-brand-50">
      <Navbar />
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="text-center text-xs text-brand-400 py-4 border-t border-brand-200">
        © {new Date().getFullYear()} RelatórioCEP — Análise de Dados com IA
      </footer>
    </div>
  );
}
