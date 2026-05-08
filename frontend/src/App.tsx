import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ChartArea as AreaChart,
  BarChart3,
  Binary,
  BookOpen,
  Boxes,
  CheckCircle2,
  CircleDot,
  Clock3,
  Database,
  Download,
  FileText,
  FlaskConical,
  GitFork,
  Grid3X3,
  History,
  ImageDown,
  LineChart,
  Loader2,
  Network,
  PieChart,
  Play,
  Radar,
  ScatterChart,
  Search,
  Settings2,
  Table2,
  Trees,
  Upload
} from "lucide-react";
import { artifactHref, createJob, fetchHistory, fetchModules, precheck } from "./api";
import type { ExportFormat, JobResult, PlotModule, PrecheckResult } from "./types";

type InputMode = "paste" | "upload" | "demo";

const exportLabels: Record<ExportFormat, string> = {
  png: "PNG",
  tiff: "TIFF",
  svg: "SVG",
  pdf: "PDF"
};

const visualKindIcons = {
  pie: PieChart,
  bar: BarChart3,
  line: LineChart,
  scatter: ScatterChart,
  distribution: Activity,
  density: Activity,
  heatmap: Grid3X3,
  matrix: Table2,
  bubble: CircleDot,
  enrichment: CircleDot,
  forest: GitFork,
  survival: Clock3,
  roc: Activity,
  pca: ScatterChart,
  set: Boxes,
  network: Network,
  hierarchy: Trees,
  funnel: BarChart3,
  genome: Binary,
  epigenome: Binary,
  pathway: GitFork,
  maf: Grid3X3,
  sequence: Binary,
  calendar: Grid3X3,
  polar: Radar,
  wordcloud: Activity,
  correlation: ScatterChart,
  qq: ScatterChart,
  radar: Radar,
  area: AreaChart,
  "dual-axis": LineChart,
  dumbbell: Activity,
  volcano: ScatterChart
} satisfies Record<PlotModule["visualKind"], typeof BarChart3>;

function ModuleIcon({ module, size = 16 }: { module: PlotModule; size?: number }) {
  const Icon = visualKindIcons[module.visualKind] ?? BarChart3;
  return <Icon size={size} aria-hidden="true" />;
}

function rendererQualityLabel(module: PlotModule) {
  if (module.rendererQuality === "plot-specific-r") return "R renderer";
  if (module.rendererQuality === "plot-specific-hybrid") return "Hybrid renderer";
  return "Python renderer";
}

function srplotParityLabel(module: PlotModule) {
  if (module.srplotParityStatus === "exact-match") return "SRplot exact";
  if (module.srplotParityStatus === "pixel-close") return "SRplot pixel-close";
  if (module.srplotParityStatus === "reference-known") return "SRplot reference";
  return "SRplot reference needed";
}

function fieldsForGroup(module: PlotModule, groupFields: string[]) {
  const wanted = new Set(groupFields);
  return module.optionFields.filter((field) => wanted.has(field.key));
}

function getSessionId() {
  const key = "hgatcplot-session-id";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  
  let next: string;
  if (typeof window.crypto.randomUUID === "function") {
    next = window.crypto.randomUUID();
  } else {
    // Fallback for non-secure contexts (HTTP on LAN)
    next = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
  
  window.localStorage.setItem(key, next);
  return next;
}

export default function App() {
  const [groups, setGroups] = useState<Record<string, PlotModule[]>>({});
  const [activeSlug, setActiveSlug] = useState("volcano");
  const [query, setQuery] = useState("");
  const [inputMode, setInputMode] = useState<InputMode>("demo");
  const [data, setData] = useState("");
  const [options, setOptions] = useState<Record<string, string | number>>({});
  const [precheckResult, setPrecheckResult] = useState<PrecheckResult | null>(null);
  const [job, setJob] = useState<JobResult | null>(null);
  const [history, setHistory] = useState<JobResult[]>([]);
  const [busy, setBusy] = useState<"loading" | "precheck" | "render" | null>("loading");
  const [notice, setNotice] = useState("");

  const sessionId = useMemo(getSessionId, []);
  const modules = useMemo(() => Object.values(groups).flat(), [groups]);
  const activeModule = modules.find((module) => module.slug === activeSlug) ?? modules[0];

  useEffect(() => {
    fetchModules()
      .then((loaded) => {
        setGroups(loaded);
        const first = Object.values(loaded).flat().find((module) => module.slug === activeSlug) ?? Object.values(loaded).flat()[0];
        if (first) {
          setActiveSlug(first.slug);
          setData(first.demoData);
          setOptions(first.defaultOptions);
        }
      })
      .finally(() => setBusy(null));
  }, []);

  useEffect(() => {
    fetchHistory(sessionId).then(setHistory);
  }, [sessionId, job?.id]);

  function selectModule(module: PlotModule) {
    setActiveSlug(module.slug);
    setInputMode("demo");
    setData(module.demoData);
    setOptions(module.defaultOptions);
    setPrecheckResult(null);
    setJob(null);
    setNotice("");
  }

  async function handleFile(file?: File) {
    if (!file) return;
    setInputMode("upload");
    setData(await file.text());
    setPrecheckResult(null);
  }

  async function runPrecheck() {
    if (!activeModule) return;
    setBusy("precheck");
    setNotice("");
    try {
      const result = await precheck(activeModule.slug, data, inputMode);
      setPrecheckResult(result);
      setNotice(result.errors.length ? "Precheck found issues to fix before rendering." : "Precheck passed. The dataset is ready to render.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Precheck failed.");
    } finally {
      setBusy(null);
    }
  }

  async function runRender() {
    if (!activeModule) return;
    setBusy("render");
    setNotice("");
    try {
      const result = await createJob(activeModule.slug, data, options, sessionId);
      setJob(result);
      setNotice(result.status === "succeeded" ? "Plot generated successfully." : "Render failed. Check validation messages.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Render failed.");
    } finally {
      setBusy(null);
    }
  }

  const filteredGroups = useMemo<Record<string, PlotModule[]>>(() => {
    const lower = query.toLowerCase();
    return Object.fromEntries(
      Object.entries(groups)
        .map(([category, items]) => [
          category,
          items.filter((module) =>
            [module.title, module.category, module.description, module.slug, module.engine, module.rendererFamily, module.sourceUrl, module.srplotReferenceUrl, module.styleProfile, ...module.aliases].some((value) => value.toLowerCase().includes(lower))
          )
        ])
        .filter(([, items]) => items.length > 0)
    ) as Record<string, PlotModule[]>;
  }, [groups, query]);

  if (!activeModule) {
    return (
      <main className="loading-screen">
        <Loader2 className="spin" />
        <span>Loading HGATCplot modules</span>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="module-rail">
        <div className="brand-lockup">
          <div className="brand-mark">
            <FlaskConical size={21} />
          </div>
          <div>
            <strong>HGATCplot</strong>
            <span>Scientific plot server</span>
          </div>
        </div>

        <label className="search-field">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search modules" />
        </label>

        <div className="module-list" aria-label="Module Library">
          <div className="section-label">Module Library</div>
          {Object.entries(filteredGroups).map(([category, items]) => (
            <section className="module-group" key={category}>
              <h2>{category}</h2>
              {items.map((module) => (
                <button
                  type="button"
                  className={module.slug === activeModule.slug ? "module-button active" : "module-button"}
                  onClick={() => selectModule(module)}
                  key={module.slug}
                >
                  <ModuleIcon module={module} />
                  <span>{module.title}</span>
                </button>
              ))}
            </section>
          ))}
        </div>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <div className="eyebrow">{activeModule.category}</div>
            <h1>{activeModule.title}</h1>
            <p>{activeModule.description}</p>
          </div>
          <div className="status-strip">
            <span><ModuleIcon module={activeModule} size={15} /> {activeModule.visualKind}</span>
            <span><CheckCircle2 size={15} /> {rendererQualityLabel(activeModule)}</span>
            <span><BookOpen size={15} /> {srplotParityLabel(activeModule)}</span>
            <span><Database size={15} /> {activeModule.requiredColumns.length} columns</span>
            <span><FlaskConical size={15} /> {activeModule.engine.toUpperCase()}</span>
            <span><ImageDown size={15} /> PNG TIFF SVG PDF</span>
          </div>
        </header>

        <div className="workflow-grid">
          <section className="input-panel">
            <div className="panel-heading">
              <div>
                <span>Step 1</span>
                <h2>Input Data</h2>
              </div>
              <div className="segmented">
                {(["demo", "paste", "upload"] as InputMode[]).map((mode) => (
                  <button
                    type="button"
                    className={inputMode === mode ? "selected" : ""}
                    onClick={() => {
                      setInputMode(mode);
                      if (mode === "demo") setData(activeModule.demoData);
                    }}
                    key={mode}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            <div className="required-row">
              {activeModule.requiredColumns.map((column) => (
                <code key={column}>{column}</code>
              ))}
            </div>

            {inputMode === "upload" ? (
              <label className="upload-box">
                <Upload size={20} />
                <span>Choose tab-delimited TXT/TSV data</span>
                <input type="file" accept=".txt,.tsv,.csv" onChange={(event) => handleFile(event.target.files?.[0])} />
              </label>
            ) : null}

            <textarea
              value={data}
              onChange={(event) => {
                setData(event.target.value);
                setPrecheckResult(null);
              }}
              spellCheck={false}
              aria-label="Tab-delimited input data"
            />

            <div className="action-row">
              <button className="primary-action" type="button" onClick={runPrecheck} disabled={busy !== null}>
                {busy === "precheck" ? <Loader2 className="spin" size={17} /> : <CheckCircle2 size={17} />}
                Precheck
              </button>
              <button className="secondary-action" type="button" onClick={() => setData(activeModule.demoData)}>
                <FileText size={17} />
                Load Demo
              </button>
            </div>
          </section>

          <section className="settings-panel">
            <div className="panel-heading">
              <div>
                <span>Step 2</span>
                <h2>Figure Options</h2>
              </div>
              <Settings2 size={19} />
            </div>

            <div className="option-groups">
              {activeModule.optionGroups.map((group) => {
                const fields = fieldsForGroup(activeModule, group.fields);
                return (
                  <section className="option-group" key={group.key}>
                    <h3>{group.label}</h3>
                    {fields.length ? (
                      <div className="option-grid">
                        {fields.map((field) => (
                          <label key={field.key} className="option-field">
                            <span>{field.label}</span>
                            {field.kind === "select" ? (
                              <select value={String(options[field.key] ?? field.default)} onChange={(event) => setOptions({ ...options, [field.key]: event.target.value })}>
                                {(field.choices ?? []).map((choice) => (
                                  <option value={choice} key={choice}>{choice}</option>
                                ))}
                              </select>
                            ) : (
                              <input
                                type={field.kind === "number" ? "number" : field.kind === "color" ? "color" : "text"}
                                value={String(options[field.key] ?? field.default)}
                                onChange={(event) => setOptions({ ...options, [field.key]: field.kind === "number" ? Number(event.target.value) : event.target.value })}
                              />
                            )}
                          </label>
                        ))}
                      </div>
                    ) : (
                      <div className="export-note">Exports are generated as PNG, TIFF, SVG, and PDF.</div>
                    )}
                  </section>
                );
              })}
            </div>

            <div className="messages" aria-live="polite">
              {notice ? <p>{notice}</p> : <p>Use tab-delimited data with decimal points for numeric values.</p>}
              {precheckResult?.warnings.map((warning) => (
                <p className="warning" key={warning}><AlertTriangle size={15} /> {warning}</p>
              ))}
              {precheckResult?.errors.map((error) => (
                <p className="error" key={error}><AlertTriangle size={15} /> {error}</p>
              ))}
            </div>

            <button className="render-action" type="button" onClick={runRender} disabled={busy !== null || (precheckResult?.errors.length ?? 0) > 0}>
              {busy === "render" ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
              Generate Plot
            </button>
          </section>

          <section className="preview-panel">
            <div className="panel-heading">
              <div>
                <span>Step 3</span>
                <h2>Preview and Downloads</h2>
              </div>
              <Download size={19} />
            </div>

            <div className="plot-preview">
              {job?.previewUrl ? (
                <img src={artifactHref(job.previewUrl)} alt={`${job.moduleTitle} preview`} />
              ) : (
                <div className="empty-preview">
                  <ModuleIcon module={activeModule} size={42} />
                  <span>Run Precheck, then Generate Plot.</span>
                </div>
              )}
            </div>

            <div className="download-grid">
              {(Object.keys(exportLabels) as ExportFormat[]).map((format) => (
                <a className={job?.artifacts[format] ? "download-button" : "download-button disabled"} href={artifactHref(job?.artifacts[format])} key={format}>
                  {exportLabels[format]}
                </a>
              ))}
            </div>
          </section>

          <section className="history-panel">
            <div className="panel-heading">
              <div>
                <span>Session History</span>
                <h2>Recent Jobs</h2>
              </div>
              <History size={19} />
            </div>
            <div className="history-list">
              {history.length ? (
                history.map((item) => (
                  <button type="button" key={item.id} onClick={() => setJob(item)}>
                    <span>{item.moduleTitle}</span>
                    <strong>{item.status}</strong>
                  </button>
                ))
              ) : (
                <p>No rendered jobs in this browser session yet.</p>
              )}
            </div>
          </section>

          <section className="paper-panel">
            <div className="panel-heading">
              <div>
                <span>Reference</span>
                <h2>Citation</h2>
              </div>
              <BookOpen size={19} />
            </div>
            <p>{activeModule.citation}</p>
            <a className="source-link" href={activeModule.sourceUrl} target="_blank" rel="noreferrer">
              SRplot source
            </a>
            <a className="source-link" href={activeModule.srplotReferenceUrl} target="_blank" rel="noreferrer">
              SRplot exact-match reference
            </a>
          </section>
        </div>
      </section>
    </main>
  );
}
