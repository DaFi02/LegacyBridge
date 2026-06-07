import { useState, useEffect } from 'react'

interface DashboardData {
  client: { name: string; contact: string; industry: string }
  project: { name: string; description: string; source_language: string; target_language: string }
  execution: { start_time: string; end_time: string; total_duration: number; status: string }
  metrics: {
    total_files: number
    total_lines: number
    total_segments: number
    segments_migrated: number
    segments_compiled: number
    compilation_rate: number
  }
  phases: Array<{
    phase: string
    status: string
    duration_seconds: number
    timestamp: string
  }>
}

interface CodePair {
  source_file: string
  target_file: string
  source_language: string
  target_language: string
  source_code: string
  target_code: string
  status: string
}

interface ExecutionResult {
  file: string
  source_file: string
  output: string
  success: boolean
  compiled: boolean
}

interface ExampleFile {
  folder: string
  file: string
  path: string
  source_lang: string
  target_lang: string
  label: string
  code: string
  lines: number
}

interface MigrationResult {
  success: boolean
  source_language: string
  target_language: string
  migrated_code: string
  model: string
  error: string | null
  output_path?: string
}

interface BrowseItem {
  name: string
  is_dir: boolean
  path: string
  size: number | null
}

interface BrowseResult {
  current: string
  parent: string | null
  items: BrowseItem[]
}

interface LoadedFolder {
  folder: string
  folder_name: string
  files: Array<{ name: string; path: string; relative: string; code: string; lines: number; extension: string }>
  total_files: number
  total_lines: number
  detected_language: string | null
  suggested_migration: string | null
}

type View = 'dashboard' | 'migrate'

function App() {
  const [view, setView] = useState<View>('migrate')
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [codePairs, setCodePairs] = useState<CodePair[]>([])
  const [execResults, setExecResults] = useState<ExecutionResult[]>([])
  const [execLoading, setExecLoading] = useState(false)

  // Migration state
  const [examples, setExamples] = useState<ExampleFile[]>([])
  const [selectedExample, setSelectedExample] = useState<ExampleFile | null>(null)
  const [migrationResult, setMigrationResult] = useState<MigrationResult | null>(null)
  const [migrating, setMigrating] = useState(false)
  const [customCode, setCustomCode] = useState('')
  const [customMigrationType, setCustomMigrationType] = useState('java7_to_python')

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8787'

  const fetchData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`)
      const json = await res.json()
      if (json.status === 'no_projects') {
        setError('No hay proyectos activos')
      } else {
        setData(json)
        setError(null)
      }
    } catch {
      setError('No se puede conectar a la API (puerto 8787)')
    } finally {
      setLoading(false)
    }
  }

  const fetchCode = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/code`)
      const json = await res.json()
      if (Array.isArray(json)) setCodePairs(json)
    } catch { /* silenciar */ }
  }

  const fetchExamples = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/examples`)
      const json = await res.json()
      if (Array.isArray(json)) setExamples(json)
    } catch { /* silenciar */ }
  }

  const fetchOutput = async () => {
    setExecLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/output`)
      const json = await res.json()
      if (Array.isArray(json)) setExecResults(json)
    } catch { /* silenciar */ }
    finally { setExecLoading(false) }
  }

  const runMigration = async (code: string, migrationType: string, filename: string) => {
    setMigrating(true)
    setMigrationResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/migrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: code, migration_type: migrationType, filename }),
      })
      const json = await res.json()
      setMigrationResult(json)
    } catch {
      setMigrationResult({ success: false, source_language: '', target_language: '', migrated_code: '', model: '', error: 'Error de conexión' })
    } finally {
      setMigrating(false)
    }
  }

  useEffect(() => {
    fetchData()
    fetchCode()
    fetchExamples()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="dashboard">
      <NavHeader view={view} setView={setView} />
      
      {view === 'migrate' ? (
        <MigrateView
          examples={examples}
          selectedExample={selectedExample}
          setSelectedExample={setSelectedExample}
          migrationResult={migrationResult}
          migrating={migrating}
          runMigration={runMigration}
          customCode={customCode}
          setCustomCode={setCustomCode}
          customMigrationType={customMigrationType}
          setCustomMigrationType={setCustomMigrationType}
          apiBase={API_BASE}
        />
      ) : (
        <>
          {loading && <div className="loading">Cargando dashboard...</div>}
          {error && <ErrorState message={error} />}
          {data && (
            <>
              <MetricsGrid metrics={data.metrics} />
              <ProgressSection metrics={data.metrics} />
              <ProjectInfo data={data} />
              <PhasesTable phases={data.phases} />
              <ExecutionSection results={execResults} loading={execLoading} onRun={fetchOutput} />
              {codePairs.length > 0 && <CodeComparison pairs={codePairs} />}
            </>
          )}
        </>
      )}
    </div>
  )
}

function NavHeader({ view, setView }: { view: View; setView: (v: View) => void }) {
  return (
    <header className="header">
      <div>
        <h1>🌉 <span>LegacyBridge</span></h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
          Migración automática de código legacy con IA
        </p>
      </div>
      <div className="nav-tabs">
        <button 
          className={`nav-tab ${view === 'migrate' ? 'active' : ''}`}
          onClick={() => setView('migrate')}
        >
          🚀 Migrar Código
        </button>
        <button 
          className={`nav-tab ${view === 'dashboard' ? 'active' : ''}`}
          onClick={() => setView('dashboard')}
        >
          📊 Dashboard
        </button>
      </div>
    </header>
  )
}

function MigrateView({
  examples, selectedExample, setSelectedExample,
  migrationResult, migrating, runMigration,
  customCode, setCustomCode, customMigrationType, setCustomMigrationType,
  apiBase,
}: {
  examples: ExampleFile[]
  selectedExample: ExampleFile | null
  setSelectedExample: (e: ExampleFile | null) => void
  migrationResult: MigrationResult | null
  migrating: boolean
  runMigration: (code: string, type: string, filename: string) => void
  customCode: string
  setCustomCode: (c: string) => void
  customMigrationType: string
  setCustomMigrationType: (t: string) => void
  apiBase: string
}) {
  const [mode, setMode] = useState<'folder' | 'examples' | 'custom'>('folder')
  const [showBrowser, setShowBrowser] = useState(false)
  const [browseData, setBrowseData] = useState<BrowseResult | null>(null)
  const [loadedFolder, setLoadedFolder] = useState<LoadedFolder | null>(null)
  const [selectedFile, setSelectedFile] = useState<number>(0)
  const [browseLoading, setBrowseLoading] = useState(false)

  const migrationTypes: Record<string, { label: string; icon: string; from: string; to: string }> = {
    java7_to_python: { label: 'Java 7 → Python 3.12', icon: '☕', from: 'Java 7', to: 'Python' },
    php_to_python: { label: 'PHP 5.4 → Python 3.12', icon: '🐘', from: 'PHP', to: 'Python' },
    html_to_react: { label: 'HTML/JS → React+Tailwind', icon: '🌐', from: 'HTML/JS', to: 'React' },
    cobol_to_rust: { label: 'COBOL → Rust', icon: '🏛️', from: 'COBOL', to: 'Rust' },
    cpp_to_rust: { label: 'C++ → Rust', icon: '⚙️', from: 'C++', to: 'Rust' },
  }

  const browseTo = async (path: string) => {
    setBrowseLoading(true)
    try {
      const res = await fetch(`${apiBase}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      const json = await res.json()
      if (!json.error) setBrowseData(json)
    } catch { /* */ }
    finally { setBrowseLoading(false) }
  }

  const openBrowser = () => {
    setShowBrowser(true)
    browseTo(loadedFolder?.folder || '/home')
  }

  const selectFolder = async (path: string) => {
    setShowBrowser(false)
    setBrowseLoading(true)
    try {
      const res = await fetch(`${apiBase}/api/load-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      const json = await res.json()
      if (!json.error) {
        setLoadedFolder(json)
        setSelectedFile(0)
        if (json.suggested_migration) {
          setCustomMigrationType(json.suggested_migration)
        }
      }
    } catch { /* */ }
    finally { setBrowseLoading(false) }
  }

  const handleMigrate = () => {
    if (mode === 'folder' && loadedFolder && loadedFolder.files.length > 0) {
      const file = loadedFolder.files[selectedFile]
      runMigration(file.code, customMigrationType, file.name)
    } else if (mode === 'examples' && selectedExample) {
      const type = `${selectedExample.source_lang}_to_${selectedExample.target_lang}`
      runMigration(selectedExample.code, type, selectedExample.file)
    } else if (mode === 'custom' && customCode.trim()) {
      runMigration(customCode, customMigrationType, 'custom_code')
    }
  }

  // Group examples by folder
  const grouped = examples.reduce((acc, ex) => {
    if (!acc[ex.folder]) acc[ex.folder] = []
    acc[ex.folder].push(ex)
    return acc
  }, {} as Record<string, ExampleFile[]>)

  return (
    <div className="migrate-view">
      {/* Mode selector */}
      <div className="migrate-mode-selector">
        <button 
          className={`mode-btn ${mode === 'folder' ? 'active' : ''}`}
          onClick={() => setMode('folder')}
        >
          💻 Abrir Proyecto
        </button>
        <button 
          className={`mode-btn ${mode === 'examples' ? 'active' : ''}`}
          onClick={() => setMode('examples')}
        >
          📁 Ejemplos
        </button>
        <button 
          className={`mode-btn ${mode === 'custom' ? 'active' : ''}`}
          onClick={() => setMode('custom')}
        >
          ✏️ Pegar Código
        </button>
      </div>

      <div className="migrate-layout">
        {/* LEFT: Input */}
        <div className="migrate-input">
          <div className="panel-header">
            <span className="panel-title">📥 INPUT — Código Legacy</span>
          </div>

          {mode === 'folder' ? (
            <div className="folder-panel">
              <button className="open-folder-btn" onClick={openBrowser}>
                <span className="folder-btn-icon">📂</span>
                <span className="folder-btn-text">
                  {loadedFolder ? 'Cambiar Carpeta' : 'Seleccionar Carpeta del Proyecto'}
                </span>
              </button>

              {loadedFolder && (
                <>
                  <div className="loaded-folder-info">
                    <div className="folder-path-display">
                      <span className="folder-icon">📁</span>
                      <span className="folder-name">{loadedFolder.folder_name}</span>
                      <span className="folder-stats">{loadedFolder.total_files} archivos · {loadedFolder.total_lines} líneas</span>
                    </div>
                    <div className="folder-path-full">{loadedFolder.folder}</div>
                  </div>

                  <div className="type-selector">
                    <label>Migración:</label>
                    <select value={customMigrationType} onChange={e => setCustomMigrationType(e.target.value)}>
                      {Object.entries(migrationTypes).map(([key, val]) => (
                        <option key={key} value={key}>{val.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="folder-files-list">
                    {loadedFolder.files.map((f, i) => (
                      <button
                        key={f.path}
                        className={`folder-file-item ${i === selectedFile ? 'selected' : ''}`}
                        onClick={() => setSelectedFile(i)}
                      >
                        <span className="file-ext">{f.extension}</span>
                        <span className="file-name">{f.relative}</span>
                        <span className="file-lines">{f.lines} lín</span>
                      </button>
                    ))}
                  </div>
                </>
              )}

              {!loadedFolder && (
                <div className="folder-empty">
                  <div className="folder-empty-icon">💻</div>
                  <p>Selecciona una carpeta de tu computadora</p>
                  <p className="folder-empty-sub">Navega y elige el proyecto legacy que quieres migrar</p>
                </div>
              )}
            </div>
          ) : mode === 'examples' ? (
            <div className="examples-panel">
              {Object.entries(grouped).map(([folder, files]) => (
                <div key={folder} className="example-group">
                  <div className="example-group-label">
                    {files[0]?.label || folder}
                  </div>
                  {files.map((ex) => (
                    <button
                      key={ex.path}
                      className={`example-item ${selectedExample?.path === ex.path ? 'selected' : ''}`}
                      onClick={() => setSelectedExample(ex)}
                    >
                      <span className="example-icon">
                        {migrationTypes[`${ex.source_lang}_to_${ex.target_lang}`]?.icon || '📄'}
                      </span>
                      <span className="example-name">{ex.file}</span>
                      <span className="example-lines">{ex.lines} líneas</span>
                    </button>
                  ))}
                </div>
              ))}
              {examples.length === 0 && (
                <div className="empty-examples">Cargando ejemplos...</div>
              )}
            </div>
          ) : (
            <div className="custom-input-panel">
              <div className="type-selector">
                <label>Tipo de migración:</label>
                <select value={customMigrationType} onChange={e => setCustomMigrationType(e.target.value)}>
                  {Object.entries(migrationTypes).map(([key, val]) => (
                    <option key={key} value={key}>{val.label}</option>
                  ))}
                </select>
              </div>
              <textarea
                className="code-input"
                placeholder="Pega tu código legacy aquí..."
                value={customCode}
                onChange={e => setCustomCode(e.target.value)}
              />
            </div>
          )}

          {/* Source code preview */}
          {mode === 'folder' && loadedFolder && loadedFolder.files.length > 0 && (
            <div className="source-preview">
              <div className="source-preview-header">
                <span>{loadedFolder.files[selectedFile].relative}</span>
                <span className="lang-badge">{loadedFolder.detected_language?.toUpperCase() || 'CODE'}</span>
              </div>
              <pre className="code-block"><code>{loadedFolder.files[selectedFile].code}</code></pre>
            </div>
          )}
          {mode === 'examples' && selectedExample && (
            <div className="source-preview">
              <div className="source-preview-header">
                <span>{selectedExample.file}</span>
                <span className="lang-badge">{selectedExample.source_lang.toUpperCase()}</span>
              </div>
              <pre className="code-block"><code>{selectedExample.code}</code></pre>
            </div>
          )}

          {/* Migrate button */}
          <button 
            className="migrate-button"
            onClick={handleMigrate}
            disabled={migrating || (
              mode === 'folder' ? !loadedFolder || loadedFolder.files.length === 0 :
              mode === 'examples' ? !selectedExample : !customCode.trim()
            )}
          >
            {migrating ? (
              <>⏳ Migrando con IA...</>
            ) : (
              <>🤖 Migrar con LLM (Llama 4 Maverick)</>
            )}
          </button>
        </div>

        {/* RIGHT: Output */}
        <div className="migrate-output">
          <div className="panel-header">
            <span className="panel-title">📤 OUTPUT — Código Moderno</span>
            {migrationResult?.model && (
              <span className="model-badge">🧠 {migrationResult.model.split('/').pop()}</span>
            )}
          </div>

          {migrating && (
            <div className="migrating-animation">
              <div className="spinner" />
              <p>Procesando con IA...</p>
              <p className="migrating-sub">NVIDIA NIM → Llama 4 Maverick 17B</p>
            </div>
          )}

          {!migrating && !migrationResult && (
            <div className="output-placeholder">
              <div className="placeholder-icon">🎯</div>
              <p>Selecciona un archivo y presiona <strong>"Migrar con LLM"</strong></p>
              <p className="placeholder-sub">El código será transformado por IA generativa</p>
            </div>
          )}

          {!migrating && migrationResult && (
            <div className={`migration-result ${migrationResult.success ? 'result-success' : 'result-error'}`}>
              {migrationResult.success ? (
                <>
                  <div className="result-header">
                    <span className="result-status">✓ MIGRACIÓN EXITOSA</span>
                    <span className="result-lang">
                      {migrationResult.source_language.toUpperCase()} → {migrationResult.target_language.toUpperCase()}
                    </span>
                  </div>
                  {migrationResult.output_path && (
                    <div className="result-path">📁 Guardado: {migrationResult.output_path}</div>
                  )}
                  <pre className="code-block output-code"><code>{migrationResult.migrated_code}</code></pre>
                </>
              ) : (
                <div className="result-error-msg">
                  <span>✗ Error: {migrationResult.error}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* File Browser Modal */}
      {showBrowser && (
        <div className="modal-overlay" onClick={() => setShowBrowser(false)}>
          <div className="modal-browser" onClick={e => e.stopPropagation()}>
            <div className="browser-header">
              <h3>📂 Seleccionar Carpeta del Proyecto</h3>
              <button className="browser-close" onClick={() => setShowBrowser(false)}>✕</button>
            </div>
            
            <div className="browser-path">
              <span className="path-label">Ubicación:</span>
              <span className="path-value">{browseData?.current || '...'}</span>
            </div>

            <div className="browser-content">
              {browseData?.parent && (
                <button className="browser-item browser-parent" onClick={() => browseTo(browseData.parent!)}>
                  <span className="item-icon">⬆️</span>
                  <span className="item-name">..</span>
                  <span className="item-type">Carpeta padre</span>
                </button>
              )}
              {browseLoading && <div className="browser-loading">Cargando...</div>}
              {browseData?.items.map((item) => (
                <button
                  key={item.path}
                  className={`browser-item ${item.is_dir ? 'browser-dir' : 'browser-file'}`}
                  onClick={() => item.is_dir && browseTo(item.path)}
                >
                  <span className="item-icon">{item.is_dir ? '📁' : '📄'}</span>
                  <span className="item-name">{item.name}</span>
                  <span className="item-type">
                    {item.is_dir ? 'Carpeta' : `${((item.size || 0) / 1024).toFixed(1)} KB`}
                  </span>
                </button>
              ))}
            </div>

            <div className="browser-footer">
              <span className="browser-hint">Navega hasta la carpeta con el código legacy</span>
              <button 
                className="browser-select-btn"
                onClick={() => browseData && selectFolder(browseData.current)}
              >
                ✓ Seleccionar esta carpeta
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricsGrid({ metrics }: { metrics: DashboardData['metrics'] }) {
  const rateColor = metrics.compilation_rate >= 80 ? 'var(--success)' : 
                    metrics.compilation_rate >= 50 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="label">Archivos</div>
        <div className="value">{metrics.total_files}</div>
        <div className="sub">{metrics.total_lines.toLocaleString()} líneas</div>
      </div>
      <div className="metric-card">
        <div className="label">Segmentos</div>
        <div className="value">{metrics.segments_migrated}/{metrics.total_segments}</div>
        <div className="sub">migrados</div>
      </div>
      <div className="metric-card">
        <div className="label">Compilación</div>
        <div className="value" style={{ color: rateColor }}>{metrics.compilation_rate.toFixed(0)}%</div>
        <div className="sub">{metrics.segments_compiled} compilan</div>
      </div>
      <div className="metric-card">
        <div className="label">Duración</div>
        <div className="value">{formatDuration(metrics.total_segments > 0 ? metrics.total_segments * 5 : 0)}</div>
        <div className="sub">tiempo estimado</div>
      </div>
    </div>
  )
}

function ProgressSection({ metrics }: { metrics: DashboardData['metrics'] }) {
  const rate = metrics.compilation_rate
  const color = rate >= 80 ? 'var(--success)' : rate >= 50 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div className="section">
      <h2>Progreso de Compilación</h2>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${rate}%`, background: color }} />
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>
        {metrics.segments_compiled} de {metrics.total_segments} segmentos compilan correctamente
      </p>
    </div>
  )
}

function ProjectInfo({ data }: { data: DashboardData }) {
  return (
    <div className="section">
      <h2>Información del Proyecto</h2>
      <div className="info-grid">
        <div className="info-item">
          <div className="label">Cliente</div>
          <div className="value">{data.client.name}</div>
        </div>
        <div className="info-item">
          <div className="label">Industria</div>
          <div className="value">{data.client.industry || '—'}</div>
        </div>
        <div className="info-item">
          <div className="label">Contacto</div>
          <div className="value">{data.client.contact || '—'}</div>
        </div>
        <div className="info-item">
          <div className="label">Migración</div>
          <div className="value">{data.project.source_language.toUpperCase()} → {data.project.target_language.toUpperCase()}</div>
        </div>
        <div className="info-item">
          <div className="label">Inicio</div>
          <div className="value">{data.execution.start_time?.slice(0, 16).replace('T', ' ') || '—'}</div>
        </div>
        <div className="info-item">
          <div className="label">Descripción</div>
          <div className="value">{data.project.description || '—'}</div>
        </div>
      </div>
    </div>
  )
}

function PhasesTable({ phases }: { phases: DashboardData['phases'] }) {
  if (!phases.length) return null

  const icons: Record<string, string> = { success: '✓', failed: '✗', skipped: '⏭', cancelled: '✗' }
  const phaseNames: Record<string, string> = {
    analyze: 'Análisis', segment: 'Segmentación', migrate: 'Migración',
    validate: 'Validación', assemble: 'Ensamblaje'
  }

  return (
    <div className="section">
      <h2>Detalle de Fases</h2>
      <table className="phases-table">
        <thead>
          <tr>
            <th>Fase</th>
            <th>Estado</th>
            <th>Duración</th>
            <th>Hora</th>
          </tr>
        </thead>
        <tbody>
          {phases.map((p, i) => (
            <tr key={i}>
              <td>{phaseNames[p.phase] || p.phase}</td>
              <td>
                <span className={`phase-status phase-${p.status}`}>
                  {icons[p.status] || '?'} {p.status.toUpperCase()}
                </span>
              </td>
              <td>{p.duration_seconds.toFixed(1)}s</td>
              <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                {p.timestamp?.slice(11, 19) || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ExecutionSection({ results, loading, onRun }: { results: ExecutionResult[]; loading: boolean; onRun: () => void }) {
  return (
    <div className="section">
      <div className="exec-header">
        <h2>🐳 Ejecución en Contenedor (Podman)</h2>
        <button className="run-button" onClick={onRun} disabled={loading}>
          {loading ? '⏳ Compilando...' : '▶ Ejecutar Binarios'}
        </button>
      </div>
      <p className="exec-description">
        Compila y ejecuta los archivos Rust migrados dentro de un contenedor aislado <code>rust:1-alpine</code>
      </p>

      {results.length === 0 && !loading && (
        <div className="exec-empty">
          Presiona <strong>"Ejecutar Binarios"</strong> para compilar y ejecutar el código migrado en Podman
        </div>
      )}

      {results.map((r, i) => (
        <div key={i} className={`exec-result ${r.success ? 'exec-success' : 'exec-error'}`}>
          <div className="exec-result-header">
            <span className="exec-icon">{r.success ? '✓' : '✗'}</span>
            <span className="exec-file">{r.source_file}</span>
            <span className="exec-arrow">→</span>
            <span className="exec-file">{r.file}</span>
            <span className={`exec-badge ${r.success ? 'badge-ok' : 'badge-err'}`}>
              {r.success ? 'EJECUTA OK' : 'ERROR'}
            </span>
          </div>
          <pre className="exec-output"><code>{r.output}</code></pre>
        </div>
      ))}
    </div>
  )
}

function CodeComparison({ pairs }: { pairs: CodePair[] }) {
  const [selected, setSelected] = useState(0)
  const pair = pairs[selected]

  return (
    <div className="section">
      <h2>Comparación de Código: Legacy → Moderno</h2>
      
      <div className="code-tabs">
        {pairs.map((p, i) => (
          <button
            key={i}
            className={`code-tab ${i === selected ? 'active' : ''}`}
            onClick={() => setSelected(i)}
          >
            <span className={`tab-status tab-${p.status}`}>
              {p.status === 'migrated' ? '✓' : '○'}
            </span>
            {p.source_file}
          </button>
        ))}
      </div>

      <div className="code-comparison">
        <div className="code-panel">
          <div className="code-panel-header">
            <span className="code-lang legacy">{pair.source_language.toUpperCase()}</span>
            <span className="code-filename">{pair.source_file}</span>
            <span className="code-badge legacy-badge">LEGACY</span>
          </div>
          <pre className="code-block"><code>{pair.source_code}</code></pre>
        </div>
        
        <div className="code-arrow">→</div>
        
        <div className="code-panel">
          <div className="code-panel-header">
            <span className="code-lang modern">{pair.target_language.toUpperCase()}</span>
            <span className="code-filename">{pair.target_file}</span>
            <span className="code-badge modern-badge">MIGRADO ✓</span>
          </div>
          <pre className="code-block"><code>{pair.target_code || '// Pendiente de migración...'}</code></pre>
        </div>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="error-state">
      <h2>Sin datos</h2>
      <p>{message}</p>
      <p style={{ marginTop: 16, fontSize: 14 }}>
        Ejecuta: <code style={{ background: 'var(--surface)', padding: '4px 8px', borderRadius: 4 }}>
          uv run python client_cli.py run --config legacybridge.toml --dashboard
        </code>
      </p>
    </div>
  )
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  return `${mins}m`
}

export default App
