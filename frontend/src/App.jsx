/**
 * App.jsx — Roteamento principal da aplicação.
 */

import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PasswordResetPage from "./pages/PasswordResetPage";
import PasswordResetConfirmPage from "./pages/PasswordResetConfirmPage";
import HistoryPage from "./pages/HistoryPage";
import ReportDetailPage from "./pages/ReportDetailPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Página principal — análise de dados (não requer login) */}
        <Route path="/" element={<HomePage />} />

        {/* Autenticação */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/password-reset" element={<PasswordResetPage />} />
        <Route path="/reset-password/:uid/:token" element={<PasswordResetConfirmPage />} />

        {/* Histórico (requer login) */}
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/history/:id" element={<ReportDetailPage />} />
      </Route>
    </Routes>
  );
}
