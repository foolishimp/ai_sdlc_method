// Implements: REQ-F-STAT-001, REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
import type { ProjectDetail, FeatureDetail, EdgeTrajectory } from '../api/types'
import { ReqLink } from './ui/ReqLink'

const EDGE_STATUS_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  converged: { icon: '✓', color: '#15803d', bg: '#dcfce7' },
  iterating: { icon: '●', color: '#1d4ed8', bg: '#dbeafe' },
  blocked:   { icon: '✗', color: '#b91c1c', bg: '#fee2e2' },
  pending:   { icon: '○', color: '#6b7280', bg: '#f3f4f6' },
}

function EdgePill({ edge }: { edge: EdgeTrajectory }) {
  const cfg = EDGE_STATUS_CONFIG[edge.status] ?? EDGE_STATUS_CONFIG.pending
  return (
    <span
      title={`${edge.edge}: ${edge.status}${edge.delta != null ? `, δ=${edge.delta}` : ''} (iter ${edge.iteration})`}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '4px',
        padding: '3px 8px', borderRadius: 'var(--radius-sm)',
        backgroundColor: cfg.bg, color: cfg.color,
        fontSize: '11px', fontWeight: 500,
        fontFamily: 'var(--font-mono)',
      }}
    >
      <span style={{ fontSize: '9px' }}>{cfg.icon}</span>
      {edge.edge}
      {edge.delta != null && edge.delta > 0 && (
        <span style={{ fontSize: '10px', opacity: 0.7 }}>δ{edge.delta}</span>
      )}
    </span>
  )
}

function FeatureRow({ feature, projectId }: { feature: FeatureDetail; projectId: string }) {
  const statusDot: Record<string, string> = {
    converged: '#22c55e', iterating: '#3b82f6', blocked: '#ef4444', pending: '#9ca3af',
  }
  const dot = statusDot[feature.status] ?? '#9ca3af'

  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      marginBottom: '8px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: dot, flexShrink: 0, marginTop: 2 }} />
          <div>
            <ReqLink reqKey={feature.feature_id} localProjectId={projectId} style={{ fontWeight: 600 }} />
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: '8px' }}>
              {feature.title}
            </span>
          </div>
        </div>
        <div style={{
          display: 'flex', gap: '8px', fontSize: '11px',
          fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }} title="Hamiltonian H = T + V">H={feature.hamiltonian.H}</span>
          <span style={{ color: 'var(--text-muted)' }}>T={feature.hamiltonian.T} V={feature.hamiltonian.V}</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', paddingLeft: '16px' }}>
        {feature.trajectory.map((edge) => (
          <EdgePill key={edge.edge} edge={edge} />
        ))}
      </div>
    </div>
  )
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{
      padding: '16px 20px', background: 'var(--surface)',
      border: '1px solid var(--border)', borderRadius: 'var(--radius)',
    }}>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>{label}</div>
      <div style={{ fontSize: '22px', fontWeight: 700, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>{sub}</div>}
    </div>
  )
}

export function StatusView({ project, projectId }: { project: ProjectDetail; projectId: string }) {
  const iterating = project.features.filter(f => f.status === 'iterating' || f.status === 'in_progress').length
  const converged = project.features.filter(f => f.status === 'converged').length
  const blocked = project.features.filter(f => f.status === 'blocked').length
  const lastEvent = project.last_event_at
    ? new Date(project.last_event_at).toLocaleString()
    : '—'

  return (
    <div data-testid="status-view">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '28px' }}>
        <StatCard label="State" value={project.state} />
        <StatCard label="Iterating" value={iterating} sub={`of ${project.features.length} features`} />
        <StatCard label="Converged" value={converged} sub={`of ${project.features.length} features`} />
        <StatCard label="Last Event" value={lastEvent} />
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Feature Trajectories</h2>
        {blocked > 0 && <span style={{ fontSize: '12px', color: '#b91c1c', fontWeight: 600 }}>{blocked} blocked</span>}
      </div>

      {project.features.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '48px 0', fontSize: '13px' }}>
          No feature vectors found.
        </div>
      ) : (
        project.features.map((f) => <FeatureRow key={f.feature_id} feature={f} projectId={projectId} />)
      )}
    </div>
  )
}
