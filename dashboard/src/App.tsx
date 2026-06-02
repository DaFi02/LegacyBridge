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

function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [codePairs, setCodePairs] = useState<CodePair[]>([])

  // En dev con proxy Vite usa /api, en producción o sin proxy usa localhost:8787
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

  useEffect(() => {
    fetchData()
    fetchCode()
    const interval = setInterval(fetchData, 3000) // Poll every 3s
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="loading">Cargando dashboard...</div>
  if (error) return <ErrorState message={error} />
  if (!data) return null

  return (
    <div className="dashboard">
      <Header data={data} />
      <MetricsGrid metrics={data.metrics} />
      <ProgressSection metrics={data.metrics} />
      <ProjectInfo data={data} />
      <PhasesTable phases={data.phases} />
      {codePairs.length > 0 && <CodeComparison pairs={codePairs} />}
    </div>
  )
}

function Header({ data }: { data: DashboardData }) {
  const statusClass = `status-badge status-${data.execution.status}`
  const statusLabel: Record<string, string> = {
    completed: '✓ Completado',
    failed: '✗ Fallido',
    in_progress: '⟳ En Progreso',
    paused: '⏸ Pausado',
  }

  return (
    <header className="header">
      <div>
        <h1>🌉 <span>LegacyBridge</span> Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
          {data.project.name} — {data.client.name}
        </p>
      </div>
      <span className={statusClass}>
        {statusLabel[data.execution.status] || data.execution.status}
      </span>
    </header>
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

function CodeComparison({ pairs }: { pairs: CodePair[] }) {
  const [selected, setSelected] = useState(0)
  const pair = pairs[selected]

  return (
    <div className="section">
      <h2>Comparación de Código: Legacy → Moderno</h2>
      
      {/* File selector tabs */}
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

      {/* Code comparison */}
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
    <div className="dashboard">
      <header className="header">
        <h1>🌉 <span style={{ color: 'var(--primary)' }}>LegacyBridge</span> Dashboard</h1>
      </header>
      <div className="error-state">
        <h2>Sin datos</h2>
        <p>{message}</p>
        <p style={{ marginTop: 16, fontSize: 14 }}>
          Ejecuta: <code style={{ background: 'var(--surface)', padding: '4px 8px', borderRadius: 4 }}>
            uv run python client_cli.py run --config legacybridge.toml --dashboard
          </code>
        </p>
      </div>
    </div>
  )
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  return `${mins}m`
}

export default App
