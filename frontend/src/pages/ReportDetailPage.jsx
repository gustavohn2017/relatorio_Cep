/**
 * ReportDetailPage.jsx — Detalhe de um relatório do histórico.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { HiArrowLeft } from "react-icons/hi";

export default function ReportDetailPage() {
  const { id } = useParams();
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/login");
      return;
    }
    if (user) fetchReport();
  }, [user, authLoading, id]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/reports/history/${id}/`);
      setReport(data);
    } catch {
      navigate("/history");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="text-center py-20 text-brand-400">Carregando...</div>
    );
  }

  if (!report) return null;

  return (
    <div className="space-y-6">
      {/* Voltar */}
      <Link
        to="/history"
        className="inline-flex items-center gap-1 text-sm text-brand-500 hover:text-brand-700"
      >
        <HiArrowLeft size={16} /> Voltar ao histórico
      </Link>

      {/* Cabeçalho */}
      <div className="bg-white border border-brand-200 rounded-xl p-6">
        <h1 className="text-xl font-bold text-brand-900 mb-2">
          {report.prompt}
        </h1>
        <p className="text-xs text-brand-400">
          Gerado em {new Date(report.created_at).toLocaleString("pt-BR")}
        </p>

        {/* Fontes usadas */}
        {report.data_sources?.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-brand-700 mb-1">
              Fontes de dados:
            </h3>
            <ul className="text-sm text-brand-500 space-y-1">
              {report.data_sources.map((ds) => (
                <li key={ds.id}>
                  • {ds.name} ({ds.source_type})
                  {ds.url && (
                    <span className="text-brand-400 ml-1 text-xs">
                      – {ds.url}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Resultado da análise */}
      <div className="bg-white border border-brand-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-brand-800 mb-4">
          Resultado da Análise
        </h2>
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.result}
          </ReactMarkdown>
        </div>
      </div>

      {/* Gráficos */}
      {report.charts?.length > 0 && (
        <div className="bg-white border border-brand-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-brand-800 mb-4">
            Gráficos
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.charts.map((chart) => (
              <div
                key={chart.id}
                className="border border-brand-200 rounded-lg overflow-hidden"
              >
                <img
                  src={chart.image}
                  alt={chart.title}
                  className="w-full"
                />
                {chart.title && (
                  <p className="text-center text-sm text-brand-500 py-2">
                    {chart.title}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
