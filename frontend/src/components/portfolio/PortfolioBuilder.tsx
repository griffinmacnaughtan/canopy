import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Plus,
  Upload,
  FileSpreadsheet,
  Building2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Download,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

interface AssetInput {
  id: string;
  name: string;
  sector: string;
  region: string;
  revenue_usd_m: number;
  scope1_tco2e: number;
  scope2_tco2e: number;
  green_revenue_pct: number;
  controversies: number;
}

interface PortfolioBuilderProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, assets: AssetInput[]) => void;
}

const SECTORS = [
  "Information Technology",
  "Energy",
  "Utilities",
  "Materials",
  "Industrials",
  "Consumer Discretionary",
  "Consumer Staples",
  "Healthcare",
  "Financials",
  "Real Estate",
  "Communication Services",
];

const REGIONS = ["North America", "Europe", "APAC", "Latin America", "Middle East & Africa"];

const SAMPLE_COMPANIES = [
  { name: "Apple Inc.", sector: "Information Technology", region: "North America" },
  { name: "Microsoft Corp.", sector: "Information Technology", region: "North America" },
  { name: "Amazon.com Inc.", sector: "Consumer Discretionary", region: "North America" },
  { name: "Tesla Inc.", sector: "Consumer Discretionary", region: "North America" },
  { name: "JPMorgan Chase", sector: "Financials", region: "North America" },
  { name: "Johnson & Johnson", sector: "Healthcare", region: "North America" },
  { name: "Exxon Mobil", sector: "Energy", region: "North America" },
  { name: "NextEra Energy", sector: "Utilities", region: "North America" },
  { name: "BASF SE", sector: "Materials", region: "Europe" },
  { name: "Toyota Motor", sector: "Consumer Discretionary", region: "APAC" },
  { name: "Samsung Electronics", sector: "Information Technology", region: "APAC" },
  { name: "Shell plc", sector: "Energy", region: "Europe" },
  { name: "Siemens AG", sector: "Industrials", region: "Europe" },
  { name: "BHP Group", sector: "Materials", region: "APAC" },
  { name: "Unilever", sector: "Consumer Staples", region: "Europe" },
];

const createEmptyAsset = (): AssetInput => ({
  id: `asset-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  name: "",
  sector: "",
  region: "",
  revenue_usd_m: 0,
  scope1_tco2e: 0,
  scope2_tco2e: 0,
  green_revenue_pct: 0,
  controversies: 0,
});

const CSV_TEMPLATE = `name,sector,region,revenue_usd_m,scope1_tco2e,scope2_tco2e,green_revenue_pct,controversies
Apple Inc.,Information Technology,North America,383000,55000,120000,42,1
Microsoft Corp.,Information Technology,North America,211000,85000,200000,38,0
Exxon Mobil,Energy,North America,413000,98000000,12000000,3,4`;

export function PortfolioBuilder({ isOpen, onClose, onSave }: PortfolioBuilderProps) {
  const [activeTab, setActiveTab] = useState<"build" | "import">("build");
  const [portfolioName, setPortfolioName] = useState("");
  const [assets, setAssets] = useState<AssetInput[]>([createEmptyAsset()]);
  const [csvData, setCsvData] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<number | null>(null);

  const addAsset = () => {
    setAssets([...assets, createEmptyAsset()]);
  };

  const removeAsset = (id: string) => {
    if (assets.length > 1) {
      setAssets(assets.filter((a) => a.id !== id));
    }
  };

  const updateAsset = (id: string, field: keyof AssetInput, value: string | number) => {
    setAssets(
      assets.map((a) =>
        a.id === id ? { ...a, [field]: value } : a
      )
    );
  };

  const selectSuggestion = (index: number, company: typeof SAMPLE_COMPANIES[0]) => {
    setAssets(
      assets.map((a, i) =>
        i === index
          ? {
              ...a,
              name: company.name,
              sector: company.sector,
              region: company.region,
              // Generate realistic mock data
              revenue_usd_m: Math.round(Math.random() * 200000 + 10000),
              scope1_tco2e: Math.round(Math.random() * 5000000 + 50000),
              scope2_tco2e: Math.round(Math.random() * 1000000 + 10000),
              green_revenue_pct: Math.round(Math.random() * 40 + 5),
              controversies: Math.floor(Math.random() * 3),
            }
          : a
      )
    );
    setShowSuggestions(null);
  };

  const validateAssets = (assetList: AssetInput[]): string[] => {
    const errs: string[] = [];
    assetList.forEach((asset, i) => {
      if (!asset.name.trim()) errs.push(`Asset ${i + 1}: Name is required`);
      if (!asset.sector) errs.push(`Asset ${i + 1}: Sector is required`);
      if (!asset.region) errs.push(`Asset ${i + 1}: Region is required`);
      if (asset.revenue_usd_m <= 0) errs.push(`Asset ${i + 1}: Revenue must be positive`);
    });
    return errs;
  };

  const parseCSV = (csv: string): AssetInput[] => {
    const lines = csv.trim().split("\n");
    if (lines.length < 2) throw new Error("CSV must have a header and at least one data row");

    const header = lines[0].toLowerCase().split(",").map((h) => h.trim());
    const requiredFields = ["name", "sector", "region", "revenue_usd_m"];
    const missing = requiredFields.filter((f) => !header.includes(f));
    if (missing.length > 0) throw new Error(`Missing required columns: ${missing.join(", ")}`);

    return lines.slice(1).map((line, i) => {
      const values = line.split(",").map((v) => v.trim());
      const getValue = (field: string) => {
        const idx = header.indexOf(field);
        return idx >= 0 ? values[idx] : "";
      };

      return {
        id: `csv-${i}-${Date.now()}`,
        name: getValue("name"),
        sector: getValue("sector"),
        region: getValue("region"),
        revenue_usd_m: parseFloat(getValue("revenue_usd_m")) || 0,
        scope1_tco2e: parseFloat(getValue("scope1_tco2e")) || 0,
        scope2_tco2e: parseFloat(getValue("scope2_tco2e")) || 0,
        green_revenue_pct: parseFloat(getValue("green_revenue_pct")) || 0,
        controversies: parseInt(getValue("controversies")) || 0,
      };
    });
  };

  const handleImport = () => {
    try {
      const parsed = parseCSV(csvData);
      const validationErrors = validateAssets(parsed);
      if (validationErrors.length > 0) {
        setErrors(validationErrors);
        return;
      }
      setAssets(parsed);
      setActiveTab("build");
      setErrors([]);
    } catch (e) {
      setErrors([e instanceof Error ? e.message : "Failed to parse CSV"]);
    }
  };

  const handleSave = () => {
    if (!portfolioName.trim()) {
      setErrors(["Portfolio name is required"]);
      return;
    }

    const validationErrors = validateAssets(assets);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    onSave(portfolioName, assets);
    onClose();
  };

  const downloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portfolio_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setCsvData(event.target?.result as string);
    };
    reader.readAsText(file);
  };

  if (!isOpen) return null;

  const filteredSuggestions = (query: string) =>
    SAMPLE_COMPANIES.filter((c) =>
      c.name.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-foreground/20 backdrop-blur-sm"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl bg-card shadow-2xl border border-border/50"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-emerald-200/50 bg-gradient-to-r from-emerald-50 via-white to-forest-50">
            <div>
              <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-forest-600 shadow-md shadow-emerald-500/20">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                Create Portfolio
              </h2>
              <p className="text-sm text-emerald-600/70 mt-1 font-medium">
                Build a custom portfolio or import from CSV
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-emerald-100 transition-colors"
            >
              <X className="h-5 w-5 text-emerald-600/60" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-emerald-200/50">
            <button
              onClick={() => setActiveTab("build")}
              className={cn(
                "flex-1 px-6 py-4 text-sm font-medium transition-all relative",
                activeTab === "build"
                  ? "text-emerald-700"
                  : "text-muted-foreground hover:text-emerald-600"
              )}
            >
              <span className="flex items-center justify-center gap-2">
                <Building2 className="h-4 w-4" />
                Build Manually
              </span>
              {activeTab === "build" && (
                <motion.div
                  layoutId="tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-forest-500"
                />
              )}
            </button>
            <button
              onClick={() => setActiveTab("import")}
              className={cn(
                "flex-1 px-6 py-4 text-sm font-medium transition-all relative",
                activeTab === "import"
                  ? "text-emerald-700"
                  : "text-muted-foreground hover:text-emerald-600"
              )}
            >
              <span className="flex items-center justify-center gap-2">
                <Upload className="h-4 w-4" />
                Import CSV
              </span>
              {activeTab === "import" && (
                <motion.div
                  layoutId="tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-forest-500"
                />
              )}
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-220px)]">
            {/* Errors */}
            <AnimatePresence>
              {errors.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20"
                >
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-destructive">Please fix the following:</p>
                      <ul className="mt-1 text-sm text-destructive/80 list-disc list-inside">
                        {errors.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Portfolio Name */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-foreground mb-2">
                Portfolio Name
              </label>
              <input
                type="text"
                value={portfolioName}
                onChange={(e) => setPortfolioName(e.target.value)}
                placeholder="e.g., My Growth Portfolio"
                className="w-full px-4 py-3 rounded-xl bg-emerald-50/50 border border-emerald-200/60 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400 transition-all"
              />
            </div>

            {activeTab === "build" ? (
              /* Build Tab */
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-foreground">
                    Holdings ({assets.length})
                  </h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addAsset}
                    className="gap-1"
                  >
                    <Plus className="h-4 w-4" />
                    Add Asset
                  </Button>
                </div>

                <div className="space-y-3">
                  {assets.map((asset, index) => (
                    <motion.div
                      key={asset.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-4 rounded-xl bg-secondary/30 border border-border/50 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Asset {index + 1}
                        </span>
                        {assets.length > 1 && (
                          <button
                            onClick={() => removeAsset(asset.id)}
                            className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {/* Company Name with Autocomplete */}
                        <div className="relative">
                          <input
                            type="text"
                            value={asset.name}
                            onChange={(e) => {
                              updateAsset(asset.id, "name", e.target.value);
                              setShowSuggestions(e.target.value.length > 0 ? index : null);
                            }}
                            onFocus={() => asset.name.length > 0 && setShowSuggestions(index)}
                            onBlur={() => setTimeout(() => setShowSuggestions(null), 200)}
                            placeholder="Company name"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                          />
                          {showSuggestions === index && filteredSuggestions(asset.name).length > 0 && (
                            <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-card rounded-lg border border-border shadow-lg overflow-hidden">
                              {filteredSuggestions(asset.name).map((company) => (
                                <button
                                  key={company.name}
                                  onClick={() => selectSuggestion(index, company)}
                                  className="w-full px-3 py-2 text-left text-sm hover:bg-primary/5 flex items-center justify-between"
                                >
                                  <span>{company.name}</span>
                                  <span className="text-xs text-muted-foreground">{company.sector}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Sector */}
                        <select
                          value={asset.sector}
                          onChange={(e) => updateAsset(asset.id, "sector", e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        >
                          <option value="">Select sector</option>
                          {SECTORS.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>

                        {/* Region */}
                        <select
                          value={asset.region}
                          onChange={(e) => updateAsset(asset.id, "region", e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
                        >
                          <option value="">Select region</option>
                          {REGIONS.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Revenue ($M)</label>
                          <input
                            type="number"
                            value={asset.revenue_usd_m || ""}
                            onChange={(e) => updateAsset(asset.id, "revenue_usd_m", parseFloat(e.target.value) || 0)}
                            placeholder="0"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Scope 1 (tCO2e)</label>
                          <input
                            type="number"
                            value={asset.scope1_tco2e || ""}
                            onChange={(e) => updateAsset(asset.id, "scope1_tco2e", parseFloat(e.target.value) || 0)}
                            placeholder="0"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Scope 2 (tCO2e)</label>
                          <input
                            type="number"
                            value={asset.scope2_tco2e || ""}
                            onChange={(e) => updateAsset(asset.id, "scope2_tco2e", parseFloat(e.target.value) || 0)}
                            placeholder="0"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Green Rev %</label>
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={asset.green_revenue_pct || ""}
                            onChange={(e) => updateAsset(asset.id, "green_revenue_pct", parseFloat(e.target.value) || 0)}
                            placeholder="0"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Controversies</label>
                          <input
                            type="number"
                            min="0"
                            max="5"
                            value={asset.controversies || ""}
                            onChange={(e) => updateAsset(asset.id, "controversies", parseInt(e.target.value) || 0)}
                            placeholder="0"
                            className="w-full px-3 py-2 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              /* Import Tab */
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Upload a CSV file or paste data below
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadTemplate}
                    className="gap-1"
                  >
                    <Download className="h-4 w-4" />
                    Download Template
                  </Button>
                </div>

                {/* File Upload */}
                <div className="relative">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-border/50 rounded-xl bg-secondary/20 hover:bg-secondary/30 transition-colors">
                    <FileSpreadsheet className="h-10 w-10 text-muted-foreground mb-3" />
                    <p className="text-sm font-medium text-foreground">Drop CSV file here or click to browse</p>
                    <p className="text-xs text-muted-foreground mt-1">Supports .csv files up to 5MB</p>
                  </div>
                </div>

                {/* CSV Textarea */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Or paste CSV data
                  </label>
                  <textarea
                    value={csvData}
                    onChange={(e) => setCsvData(e.target.value)}
                    placeholder={CSV_TEMPLATE}
                    rows={8}
                    className="w-full px-4 py-3 rounded-xl bg-secondary/50 border border-border/50 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary font-mono text-xs"
                  />
                </div>

                <Button
                  onClick={handleImport}
                  disabled={!csvData.trim()}
                  className="w-full gap-2"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Parse & Preview
                </Button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-emerald-200/50 bg-gradient-to-r from-emerald-50/50 to-forest-50/50">
            <p className="text-sm text-emerald-600/80 font-medium">
              {assets.length} asset{assets.length !== 1 ? "s" : ""} in portfolio
            </p>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={onClose} className="border-emerald-200 hover:bg-emerald-50 hover:border-emerald-300">
                Cancel
              </Button>
              <Button onClick={handleSave} className="gap-2 bg-gradient-to-r from-emerald-500 to-forest-600 hover:from-emerald-600 hover:to-forest-700 shadow-lg shadow-emerald-500/25">
                Create Portfolio
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
