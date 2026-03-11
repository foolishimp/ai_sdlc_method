// Implements: REQ-F-GAP-001, REQ-F-GAP-002, REQ-F-GAP-003, REQ-F-GAP-004
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const LAYER_NAMES: Record<number, string> = {
  1: 'REQ Tag Coverage',
  2: 'Test Gap Analysis',
  3: 'Telemetry Gap Analysis',
}

export function GapView({ projectId }: { projectId: string }) {
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['gaps', projectId],
    queryFn: () => api.getGaps(projectId),
  })

  if (isLoading) return <div>Loading gap report…</div>
  if (error) return <div style={{ color: '#dc2626' }}>Error: {String(error)}</div>
  if (!report) return null

  return (
    <div data-testid="gap-view">
      <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Total REQ Keys</div>
          <div style={{ fontWeight: 'bold', fontSize: '1.25rem' }}>{report.total_req_keys}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Covered</div>
          <div style={{ fontWeight: 'bold', fontSize: '1.25rem', color: '#16a34a' }}>{report.covered_count}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Gaps</div>
          <div style={{ fontWeight: 'bold', fontSize: '1.25rem', color: report.gap_count > 0 ? '#dc2626' : '#16a34a' }}>{report.gap_count}</div>
        </div>
      </div>

      {report.layers.map((layer) => (
        <div key={layer.layer} style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Layer {layer.layer}: {LAYER_NAMES[layer.layer] ?? ''}
            <span style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              backgroundColor: layer.status === 'pass' ? '#d1fae5' : layer.status === 'advisory' ? '#fef3c7' : '#fee2e2',
              color: layer.status === 'pass' ? '#065f46' : layer.status === 'advisory' ? '#92400e' : '#991b1b',
            }}>
              {layer.status.toUpperCase()}
            </span>
          </h3>
          {layer.gaps.length === 0 ? (
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>No gaps in this layer.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left' }}>
                  <th style={{ padding: '8px 4px' }}>REQ Key</th>
                  <th style={{ padding: '8px 4px' }}>Severity</th>
                  <th style={{ padding: '8px 4px' }}>Description</th>
                </tr>
              </thead>
              <tbody>
                {layer.gaps.map((gap) => (
                  <tr key={`${gap.layer}-${gap.req_key}`} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '8px 4px', fontFamily: 'monospace', fontSize: '0.8rem' }}>{gap.req_key}</td>
                    <td style={{ padding: '8px 4px' }}>
                      <span style={{
                        color: gap.severity === 'high' ? '#dc2626' : gap.severity === 'medium' ? '#d97706' : '#6b7280',
                        fontWeight: 'bold', fontSize: '0.75rem',
                      }}>{gap.severity}</span>
                    </td>
                    <td style={{ padding: '8px 4px', color: '#374151' }}>{gap.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  )
}
