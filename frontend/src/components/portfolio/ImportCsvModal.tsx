import { useState, useCallback, useRef } from "react";
import { Upload, FileText, X, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { usePortfolioContext } from "@/contexts/PortfolioContext";
import { toast } from "sonner";

interface ImportCsvModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CSV_TEMPLATE = [
  "name,ticker,sector,region,revenue_usd_m,scope1_tco2e,scope2_tco2e,green_revenue_pct,controversies",
  "Acme Solar,ACME,Energy,North America,2500,80000,20000,60,1",
  "GreenTech Inc,,Information Technology,Europe,1200,5000,15000,75,0",
  "Pacific Utilities,PCU,Utilities,APAC,800,4200000,900000,45,2",
].join("\n");

export function ImportCsvModal({ isOpen, onClose }: ImportCsvModalProps) {
  const { setSelectedPortfolioId } = usePortfolioContext();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [portfolioName, setPortfolioName] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    rows_imported: number;
    rows_skipped: number;
    warnings: string[];
    portfolio_id: string;
    portfolio_name: string;
  } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const resetState = () => {
    setFile(null);
    setPortfolioName("");
    setResult(null);
    setIsDragging(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith(".csv")) {
      toast.error("Only .csv files are supported");
      return;
    }
    setFile(f);
    setResult(null);
    if (!portfolioName) {
      setPortfolioName(f.name.replace(".csv", "").replace(/_/g, " "));
    }
  };

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) handleFile(dropped);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [portfolioName]
  );

  const handleImport = async () => {
    if (!file) return;
    setIsImporting(true);
    try {
      const nameParam = portfolioName.trim() || undefined;
      const resp = await api.importCsv(file, nameParam);
      setResult({
        success: resp.success,
        rows_imported: resp.rows_imported,
        rows_skipped: resp.rows_skipped,
        warnings: resp.warnings,
        portfolio_id: resp.portfolio.id,
        portfolio_name: resp.portfolio.name,
      });
      if (resp.success) {
        toast.success(
          `Imported "${resp.portfolio.name}" — ${resp.rows_imported} assets`
        );
        await queryClient.invalidateQueries({ queryKey: ["portfolios"] });
        setSelectedPortfolioId(resp.portfolio.id);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Import failed";
      toast.error(msg);
    } finally {
      setIsImporting(false);
    }
  };

  const downloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "canopy_portfolio_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg rounded-2xl bg-white shadow-2xl border border-emerald-100">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Import from CSV</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Bulk-import assets from a spreadsheet
            </p>
          </div>
          <button
            onClick={handleClose}
            className="rounded-lg p-1.5 hover:bg-gray-100 transition-colors"
          >
            <X className="h-4 w-4 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Template download */}
          <button
            onClick={downloadTemplate}
            className="w-full flex items-center gap-3 p-3 rounded-xl border border-dashed border-emerald-300 bg-emerald-50/50 hover:bg-emerald-50 transition-colors text-sm text-emerald-700"
          >
            <FileText className="h-4 w-4 shrink-0" />
            <span>Download CSV template with required columns</span>
          </button>

          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all ${
              isDragging
                ? "border-emerald-400 bg-emerald-50"
                : file
                ? "border-emerald-300 bg-emerald-50/30"
                : "border-gray-200 hover:border-emerald-300 hover:bg-gray-50"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              className="sr-only"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            <Upload className={`mx-auto h-8 w-8 mb-2 ${file ? "text-emerald-500" : "text-gray-300"}`} />
            {file ? (
              <div>
                <p className="text-sm font-semibold text-emerald-700">{file.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB — click to change
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Drop your CSV here, or <span className="text-emerald-600">browse</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">Supports UTF-8 CSV up to 5 MB</p>
              </div>
            )}
          </div>

          {/* Portfolio name */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1.5">
              Portfolio name <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="text"
              value={portfolioName}
              onChange={(e) => setPortfolioName(e.target.value)}
              placeholder="Defaults to filename"
              maxLength={100}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400"
            />
          </div>

          {/* Result */}
          {result && (
            <div className={`rounded-xl p-4 text-sm ${result.success ? "bg-emerald-50 border border-emerald-200" : "bg-red-50 border border-red-200"}`}>
              <div className="flex items-center gap-2 font-semibold mb-1">
                {result.success ? (
                  <><CheckCircle2 className="h-4 w-4 text-emerald-600" /><span className="text-emerald-700">Import successful</span></>
                ) : (
                  <><AlertCircle className="h-4 w-4 text-red-500" /><span className="text-red-700">Import failed</span></>
                )}
              </div>
              {result.success && (
                <p className="text-emerald-600">
                  {result.rows_imported} assets imported to "{result.portfolio_name}"
                  {result.rows_skipped > 0 && `, ${result.rows_skipped} rows skipped`}.
                </p>
              )}
              {result.warnings.length > 0 && (
                <ul className="mt-2 space-y-0.5 text-amber-700 text-xs">
                  {result.warnings.slice(0, 5).map((w, i) => (
                    <li key={i} className="flex gap-1"><span>⚠</span>{w}</li>
                  ))}
                  {result.warnings.length > 5 && (
                    <li className="text-gray-400">…and {result.warnings.length - 5} more warnings</li>
                  )}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 pb-6 pt-0">
          <button
            onClick={handleClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
          >
            {result?.success ? "Close" : "Cancel"}
          </button>
          {!result?.success && (
            <button
              onClick={handleImport}
              disabled={!file || isImporting}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isImporting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isImporting ? "Importing…" : "Import Portfolio"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
