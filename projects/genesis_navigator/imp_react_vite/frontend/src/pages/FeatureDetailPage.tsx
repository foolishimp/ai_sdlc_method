// Implements: REQ-F-FEATDETAIL-001
import { useParams, useNavigate } from 'react-router'
import { ReqLink } from '../components/ui/ReqLink'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const STATUS_COLORS: Record<string, string> = {
  converged: 'var(--state-converged)',
  iterating: 'var(--state-iterating)',
  in_progress: 'var(--state-iterating)',
  pending: 'var(--text-muted)',
  blocked: 'var(--state-blocked)',
  stuck: 'var(--state-stuck)',
  error: '#ef4444',
}

const EDGE_ICONS: Record<string, string> = {
  converged: '✓',
  in_progress: '●',
  iterating: '●',
  pending: '○',
  blocked: '✗',
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '11px',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      background: (STATUS_COLORS[status] ?? 'var(--text-muted)') + '22',
      color: STATUS_COLORS[status] ?? 'var(--text-muted)',
      border: `1px solid ${(STATUS_COLORS[status] ?? 'var(--text-muted)') + '44'}`,
    }}>
      {status}
    </span>
  )
}

function HamiltonianBadge({ H, T, V, flat }: { H: number; T: number; V: number; flat: boolean }) {
  return (
    <span style={{ display: 'inline-flex', gap: '12px', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
      <span title="H = total work cost (T+V)">
        <span style={{ color: 'var(--text-muted)' }}>H=</span>
        <span style={{ fontWeight: 600, color: flat ? 'var(--state-stuck)' : 'var(--accent)' }}>{H}</span>
      </span>
      <span title="T = iterations completed">
        <span style={{ color: 'var(--text-muted)' }}>T=</span>
        <span style={{ color: 'var(--text-primary)' }}>{T}</span>
      </span>
      <span title="V = remaining delta">
        <span style={{ color: 'var(--text-muted)' }}>V=</span>
        <span style={{ color: V > 0 ? 'var(--state-stuck)' : 'var(--state-converged)' }}>{V}</span>
      </span>
      {flat && <span style={{ color: 'var(--state-stuck)', fontSize: '11px' }}>⚠ stalled</span>}
    </span>
  )
}

export function FeatureDetailPage() {
  const { id, featureId } = useParams<{ id: string; featureId: string }>()
  const navigate = useNavigate()
  const projectId = id ?? ''
  const fid = featureId ?? ''

  const { data: feature, isLoading, error } = useQuery({
    queryKey: ['feature', projectId, fid],
    queryFn: () => api.getFeature(projectId, fid),
    enabled: !!(projectId && fid),
  })

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <div style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        padding: '0 32px',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', height: '56px' }}>
            <button
              onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}`)}
              style={{
                display: 'flex', alignItems: 'center', gap: '4px',
                padding: '4px 10px', borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)', background: 'transparent',
                color: 'var(--text-secondary)', fontSize: '13px',
              }}
            >
              ← {projectId}
            </button>
            <span style={{ color: 'var(--text-muted)' }}>/</span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: '13px',
              color: 'var(--accent)', fontWeight: 600,
            }}>
              {fid}
            </span>
            {feature && <StatusBadge status={feature.status} />}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px' }}>
        {isLoading && (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '64px 0' }}>
            Loading feature…
          </div>
        )}
        {error && (
          <div style={{
            padding: '24px 28px',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
          }}>
            <div style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: 'var(--accent)', marginBottom: '8px' }}>
              {fid}
            </div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
              No feature vector found
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <strong>{fid}</strong> is a requirement key defined in the spec, but no feature vector has been
              created for it yet. To build it, run:
            </div>
            <div style={{
              marginTop: '12px', padding: '10px 14px',
              background: 'var(--surface-2)', borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--accent)',
            }}>
              /gen-spawn --feature "{fid}"
            </div>
          </div>
        )}

        {feature && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Title card */}
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
                    {feature.feature_id}
                  </div>
                  <h1 style={{ margin: '0 0 12px 0', fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {feature.title}
                  </h1>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                    <StatusBadge status={feature.status} />
                    {feature.current_edge && (
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        edge: {feature.current_edge}
                      </span>
                    )}
                    <HamiltonianBadge
                      H={feature.hamiltonian.H}
                      T={feature.hamiltonian.T}
                      V={feature.hamiltonian.V}
                      flat={feature.hamiltonian.flat}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* Satisfies */}
              {(feature.satisfies?.length ?? 0) > 0 && (
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '20px' }}>
                  <h2 style={{ margin: '0 0 16px 0', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Satisfies
                  </h2>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {feature.satisfies!.map((key) => (
                      <ReqLink key={key} reqKey={key} localProjectId={projectId} />
                    ))}
                  </div>
                </div>
              )}

              {/* Trajectory */}
              {feature.trajectory.length > 0 && (
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '20px' }}>
                  <h2 style={{ margin: '0 0 16px 0', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Trajectory
                  </h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {feature.trajectory.map((edge) => (
                      <div key={edge.edge} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px' }}>
                        <span style={{
                          color: STATUS_COLORS[edge.status] ?? 'var(--text-muted)',
                          fontSize: '14px', width: '16px', textAlign: 'center',
                        }}>
                          {EDGE_ICONS[edge.status] ?? '○'}
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', flex: 1, color: 'var(--text-primary)' }}>
                          {edge.edge}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {edge.iteration > 0 ? `${edge.iteration}×` : ''}
                        </span>
                        {edge.delta > 0 && (
                          <span style={{ fontSize: '11px', color: 'var(--state-stuck)' }}>δ={edge.delta}</span>
                        )}
                        {edge.converged_at && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {new Date(edge.converged_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Acceptance criteria */}
            {(feature.acceptance_criteria?.length ?? 0) > 0 && (
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '20px' }}>
                <h2 style={{ margin: '0 0 16px 0', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Acceptance Criteria
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {feature.acceptance_criteria!.map((ac, i) => (
                    <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', fontSize: '13px', color: 'var(--text-primary)' }}>
                      <span style={{ color: 'var(--state-converged)', marginTop: '1px', flexShrink: 0 }}>✓</span>
                      <span>{ac}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
