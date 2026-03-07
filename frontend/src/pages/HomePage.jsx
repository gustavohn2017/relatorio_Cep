/**
 * HomePage.jsx — Página principal de análise de dados.
 *
 * Permite ao usuário:
 *  - Adicionar links de Google Sheets (com seleção de aba)
 *  - Enviar arquivos (CSV, Excel, PDF, XML, TXT)
 *  - Digitar um prompt para a IA analisar
 *  - Solicitar geração de gráficos
 *  - Ver resultado em Markdown com gráficos embutidos
 */

import { useState } from "react";
import api from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  HiPlus,
  HiTrash,
  HiUpload,
  HiLightningBolt,
  HiChartBar,
} from "react-icons/hi";

export default function HomePage() {
  // Estado das fontes de dados
  const [sheetLinks, setSheetLinks] = useState([{ url: "", tab: "", tabs: [] }]);
  const [files, setFiles] = useState([]);
  const [uploadedSourceIds, setUploadedSourceIds] = useState([]);

  // Prompt e configurações
  const [prompt, setPrompt] = useState("");
  const [generateCharts, setGenerateCharts] = useState(false);

  // Resultado
  const [result, setResult] = useState(null);
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // E-mail do Service Account (para compartilhamento)
  const [serviceEmail, setServiceEmail] = useState("");
  const [loadingEmail, setLoadingEmail] = useState(false);

  // -------------------------------------------------------
  // Google Sheets — gerenciar links
  // -------------------------------------------------------
  const addSheetLink = () =>
    setSheetLinks([...sheetLinks, { url: "", tab: "", tabs: [] }]);

  const removeSheetLink = (idx) =>
    setSheetLinks(sheetLinks.filter((_, i) => i !== idx));

  const updateSheetLink = (idx, field, value) => {
    const updated = [...sheetLinks];
    updated[idx][field] = value;
    setSheetLinks(updated);
  };

  // Buscar abas de uma planilha
  const fetchTabs = async (idx) => {
    const url = sheetLinks[idx].url;
    if (!url) return;
    try {
      const { data } = await api.post("/reports/sheets/tabs/", { url });
      const updated = [...sheetLinks];
      updated[idx].tabs = data.tabs;
      if (data.tabs.length > 0) {
        updated[idx].tab = data.tabs[0].title;
      }
      setSheetLinks(updated);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Não foi possível acessar a planilha."
      );
    }
  };

  // Buscar e-mail do Service Account
  const fetchServiceEmail = async () => {
    setLoadingEmail(true);
    try {
      const { data } = await api.get("/reports/sheets/email/");
      setServiceEmail(data.email);
    } catch {
      setServiceEmail("Erro ao buscar e-mail.");
    } finally {
      setLoadingEmail(false);
    }
  };

  // -------------------------------------------------------
  // Upload de arquivos
  // -------------------------------------------------------
  const handleFileChange = (e) => {
    setFiles([...files, ...Array.from(e.target.files)]);
  };

  const removeFile = (idx) => setFiles(files.filter((_, i) => i !== idx));

  const uploadFiles = async () => {
    const ids = [];
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", file.name);
      const { data } = await api.post("/reports/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      ids.push(data.id);
    }
    setUploadedSourceIds(ids);
    return ids;
  };

  // -------------------------------------------------------
  // Executar análise
  // -------------------------------------------------------
  const handleAnalyze = async () => {
    if (!prompt.trim()) {
      setError("Digite uma pergunta ou instrução para a análise.");
      return;
    }

    const activeLinks = sheetLinks.filter((s) => s.url.trim());
    if (activeLinks.length === 0 && files.length === 0 && uploadedSourceIds.length === 0) {
      setError("Adicione pelo menos um link do Google Sheets ou envie um arquivo.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setCharts([]);

    try {
      // Upload de arquivos novos, se houver
      let sourceIds = [...uploadedSourceIds];
      if (files.length > 0) {
        const newIds = await uploadFiles();
        sourceIds = [...sourceIds, ...newIds];
      }

      // Monta payload
      const payload = {
        prompt,
        generate_charts: generateCharts,
        source_urls: activeLinks.map((s) => s.url),
        sheet_tabs: activeLinks.map((s) => s.tab),
        source_ids: sourceIds,
      };

      const { data } = await api.post("/reports/analyze/", payload);
      setResult(data.report);
      setCharts(data.charts || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Erro ao processar análise. Verifique os dados e tente novamente."
      );
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------
  // Render
  // -------------------------------------------------------
  return (
    <div className="space-y-8">
      {/* Cabeçalho */}
      <div>
        <h1 className="text-2xl font-bold text-brand-900">Análise de Dados</h1>
        <p className="text-brand-500 mt-1">
          Adicione fontes de dados e faça perguntas — a IA analisa e gera
          relatórios detalhados.
        </p>
      </div>

      {/* ---- Seção: Google Sheets ---- */}
      <section className="bg-white rounded-xl border border-brand-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-brand-800">
            Google Sheets
          </h2>
          <button
            onClick={fetchServiceEmail}
            className="text-xs text-brand-500 hover:text-brand-700 underline"
          >
            {loadingEmail
              ? "Carregando..."
              : "Ver e-mail para compartilhamento"}
          </button>
        </div>

        {serviceEmail && (
          <div className="bg-brand-100 p-3 rounded-lg text-sm">
            <strong>Compartilhe suas planilhas com:</strong>{" "}
            <span className="font-mono text-brand-700">{serviceEmail}</span>
            <p className="text-brand-400 text-xs mt-1">
              Abra a planilha → Compartilhar → adicione este e-mail como leitor.
            </p>
          </div>
        )}

        {sheetLinks.map((link, idx) => (
          <div key={idx} className="flex flex-col sm:flex-row gap-3">
            <input
              type="url"
              placeholder="https://docs.google.com/spreadsheets/d/..."
              value={link.url}
              onChange={(e) => updateSheetLink(idx, "url", e.target.value)}
              className="flex-1 px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
            <button
              onClick={() => fetchTabs(idx)}
              className="px-3 py-2 text-sm bg-brand-200 rounded-lg hover:bg-brand-300 transition whitespace-nowrap"
            >
              Buscar abas
            </button>
            {link.tabs.length > 0 && (
              <select
                value={link.tab}
                onChange={(e) => updateSheetLink(idx, "tab", e.target.value)}
                className="px-3 py-2 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              >
                {link.tabs.map((t) => (
                  <option key={t.title} value={t.title}>
                    {t.title} ({t.rows}×{t.cols})
                  </option>
                ))}
              </select>
            )}
            {sheetLinks.length > 1 && (
              <button
                onClick={() => removeSheetLink(idx)}
                className="text-red-500 hover:text-red-700 p-2"
                title="Remover"
              >
                <HiTrash size={18} />
              </button>
            )}
          </div>
        ))}

        <button
          onClick={addSheetLink}
          className="flex items-center gap-1 text-sm text-brand-500 hover:text-brand-700"
        >
          <HiPlus size={16} /> Adicionar outro link
        </button>
      </section>

      {/* ---- Seção: Upload de Arquivos ---- */}
      <section className="bg-white rounded-xl border border-brand-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-brand-800">
          Upload de Arquivos
        </h2>
        <p className="text-sm text-brand-400">
          CSV, Excel (.xlsx), XML, PDF ou Texto (.txt)
        </p>

        <label className="inline-flex items-center gap-2 cursor-pointer px-4 py-2 border-2 border-dashed border-brand-300 rounded-lg text-sm text-brand-500 hover:border-brand-400 hover:text-brand-700 transition">
          <HiUpload size={18} />
          Selecionar arquivos
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls,.xml,.pdf,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        {files.length > 0 && (
          <ul className="space-y-1">
            {files.map((f, idx) => (
              <li
                key={idx}
                className="flex items-center justify-between bg-brand-50 px-3 py-2 rounded text-sm"
              >
                <span className="truncate">{f.name}</span>
                <button
                  onClick={() => removeFile(idx)}
                  className="text-red-500 hover:text-red-700 ml-2"
                >
                  <HiTrash size={16} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* ---- Seção: Prompt ---- */}
      <section className="bg-white rounded-xl border border-brand-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-brand-800">
          Sua Pergunta / Instrução
        </h2>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ex: Compare as vendas do primeiro semestre entre as duas planilhas e destaque as principais diferenças. Gere um gráfico de barras comparativo."
          rows={4}
          className="w-full px-4 py-3 border border-brand-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-y"
        />

        <label className="flex items-center gap-2 text-sm text-brand-600 cursor-pointer">
          <input
            type="checkbox"
            checked={generateCharts}
            onChange={(e) => setGenerateCharts(e.target.checked)}
            className="rounded accent-brand-700"
          />
          <HiChartBar size={16} /> Gerar gráficos automaticamente
        </label>
      </section>

      {/* Erro */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Botão de análise */}
      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 bg-brand-800 text-white rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
      >
        {loading ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            Analisando...
          </>
        ) : (
          <>
            <HiLightningBolt size={20} /> Analisar com IA
          </>
        )}
      </button>

      {/* ---- Resultado ---- */}
      {result && (
        <section className="bg-white rounded-xl border border-brand-200 p-6 space-y-6">
          <h2 className="text-lg font-semibold text-brand-800">
            Resultado da Análise
          </h2>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.result}
            </ReactMarkdown>
          </div>

          {/* Gráficos */}
          {charts.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-md font-semibold text-brand-700">
                Gráficos Gerados
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {charts.map((chart, idx) => (
                  <div
                    key={idx}
                    className="border border-brand-200 rounded-lg overflow-hidden"
                  >
                    {chart.error ? (
                      <div className="p-4 text-red-600 text-sm">
                        Erro: {chart.error}
                      </div>
                    ) : (
                      <>
                        <img
                          src={chart.image_url}
                          alt={chart.title}
                          className="w-full"
                        />
                        {chart.title && (
                          <p className="text-center text-sm text-brand-500 py-2">
                            {chart.title}
                          </p>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
