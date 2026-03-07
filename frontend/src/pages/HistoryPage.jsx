/**
 * HistoryPage.jsx — Histórico de relatórios do usuário autenticado.
 */

import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { HiTrash, HiEye } from "react-icons/hi";

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/login");
      return;
    }
    if (user) fetchReports();
  }, [user, authLoading]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/reports/history/");
      setReports(data.results || data);
    } catch {
      /* vazio */
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (id) => {
    if (!window.confirm("Tem certeza que deseja excluir este relatório?")) return;
    try {
      await api.delete(`/reports/history/${id}/`);
      setReports(reports.filter((r) => r.id !== id));
    } catch {
      /* vazio */
    }
  };

  if (authLoading || loading) {
    return (
      <div className="text-center py-20 text-brand-400">Carregando...</div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-900">
        Histórico de Análises
      </h1>

      {reports.length === 0 ? (
        <div className="text-center py-16 text-brand-400">
          <p className="text-lg">Nenhum relatório encontrado.</p>
          <Link
            to="/"
            className="inline-block mt-4 px-4 py-2 bg-brand-800 text-white rounded-lg text-sm hover:bg-brand-700 transition"
          >
            Fazer uma análise
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="flex items-center justify-between bg-white border border-brand-200 rounded-lg px-5 py-4"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-brand-800 truncate">
                  {report.prompt}
                </p>
                <p className="text-xs text-brand-400 mt-1">
                  {new Date(report.created_at).toLocaleString("pt-BR")} •{" "}
                  {report.data_sources?.length || 0} fonte(s) •{" "}
                  {report.charts?.length || 0} gráfico(s)
                </p>
              </div>

              <div className="flex items-center gap-2 ml-4">
                <Link
                  to={`/history/${report.id}`}
                  className="p-2 text-brand-500 hover:text-brand-700 transition"
                  title="Ver detalhes"
                >
                  <HiEye size={18} />
                </Link>
                <button
                  onClick={() => deleteReport(report.id)}
                  className="p-2 text-red-400 hover:text-red-600 transition"
                  title="Excluir"
                >
                  <HiTrash size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
