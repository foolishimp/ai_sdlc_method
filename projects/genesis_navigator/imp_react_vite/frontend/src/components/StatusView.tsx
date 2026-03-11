// Implements: REQ-F-STAT-001, REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
import type { ProjectDetail, FeatureDetail } from '../api/types'

function TrajectoryBar({ feature }: { feature: FeatureDetail }) {
  const icons: Record<string, string> = {
    pending: '○',
    iterating: '●',
    converged: '✓',
    blocked: '✗',
  }
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '4px' }}>
        <span style={{ fontWeight: 'bold' }}>{feature.feature_id}</span>
        <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>{feature.title}</span>
        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>H={feature.hamiltonian_h} (T={feature.hamiltonian_t}+V={feature.hamiltonian_v})</span>
      </div>
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
        {feature.trajectory.map((edge) => (
          <span
            key={edge.edge}
            title={`${edge.edge}: ${edge.status} (iter ${edge.iteration})`}
            style={{
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '0.7rem',
              backgroundColor: edge.status === 'converged' ? '#d1fae5' : edge.status === 'iterating' ? '#dbeafe' : edge.status === 'blocked' ? '#fee2e2' : '#f3f4f6',
              color: edge.status === 'converged' ? '#065f46' : edge.status === 'iterating' ? '#1e40af' : edge.status === 'blocked' ? '#991b1b' : '#374151',
            }}
          >
            {icons[edge.status] ?? '?'} {edge.edge}
          </span>
        ))}
      </div>
    </div>
  )
}

export function StatusView({ project }: { project: ProjectDetail }) {
  const stateColor: Record<string, string> = {
    ITERATING: '#2563eb',
    QUIESCENT: '#d97706',
    CONVERGED: '#16a34a',
    BOUNDED: '#7c3aed',
  }

  return (
    <div data-testid="status-view">
      <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', minWidth: '120px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '4px' }}>State</div>
          <div style={{ fontWeight: 'bold', color: stateColor[project.state] ?? '#374151' }}>{project.state}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', minWidth: '120px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '4px' }}>Features</div>
          <div style={{ fontWeight: 'bold' }}>{project.features.length}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', minWidth: '120px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '4px' }}>Last Event</div>
          <div style={{ fontSize: '0.875rem' }}>{project.last_event_at ? new Date(project.last_event_at).toLocaleDateString() : '—'}</div>
        </div>
      </div>

      <h2 style={{ fontSize: '1rem', marginBottom: '16px' }}>Feature Trajectories</h2>
      {project.features.map((f) => (
        <TrajectoryBar key={f.feature_id} feature={f} />
      ))}
      {project.features.length === 0 && <p style={{ color: '#6b7280' }}>No feature vectors found.</p>}
    </div>
  )
}
