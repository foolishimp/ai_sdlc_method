// Implements: REQ-F-GAP-001, REQ-F-GAP-002, REQ-F-GAP-003, REQ-F-GAP-004
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { BackendGapLayer } from '../api/types'
import { LoadingConsole } from './LoadingConsole'
import { ReqLink } from './ui/ReqLink'

const GAP_MESSAGES = [
  'Reading .ai-workspace/features/active/*.yml',
  'Scanning source files for # Implements: REQ-* tags',
  'Scanning test files for # Validates: REQ-* tags',
  'Computing Layer 1 — REQ tag coverage',
  'Computing Layer 2 — test gap analysis',
  'Computing Layer 3 — telemetry gap analysis',
  'Aggregating gap report',
]

const LAYER_META = [
  { key: 'layer_1' as const, num: 1, name: 'REQ Tag Coverage',       advisory: false },
  { key: 'layer_2' as const, num: 2, name: 'Test Gap Analysis',      advisory: false },
  { key: 'layer_3' as const, num: 3, name: 'Telemetry Gap Analysis', advisory: true  },
]

const HEALTH_COLORS: Record<string, string> = {
  GREEN: '#22c55e', YELLOW: '#eab308', RED: '#ef4444',
}

function LayerSection({ meta, layer, pSlug }: { meta: typeof LAYER_META[number]; layer: BackendGapLayer; pSlug: string }) {
  const status = layer.gap_count === 0 ? 'PASS' : meta.advisory ? 'ADVISORY' : 'FAIL'
  const statusColors: Record<string, { bg: string; text: string }> = {
    PASS:     { bg: 'var(--state-converged-bg)',    text: 'var(--state-converged-text)' },
    FAIL:     { bg: 'var(--stuck-bg)',              text: 'var(--stuck-text)' },
    ADVISORY: { bg: 'var(--state-quiescent-bg)',    text: 'var(--state-quiescent-text)' },
  }
  const sc = statusColors[status]!

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <div style={{
          width: 24, height: 24, borderRadius: '6px',
          background: 'var(--surface-2)', border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)',
        }}>{meta.num}</div>
        <span style={{ fontWeight: 600, fontSize: '14px' }}>{meta.name}</span>
        <span style={{ padding: '2px 8px', borderRadius: '100px', backgroundColor: sc.bg, color: sc.text, fontSize: '11px', fontWeight: 600 }}>
          {status}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {layer.coverage_pct.toFixed(1)}% coverage · {layer.gap_count} gap{layer.gap_count !== 1 ? 's' : ''}
        </span>
      </div>

      {layer.gaps.length === 0 ? (
        <div style={{
          padding: '12px 16px',
          background: 'var(--state-converged-bg)',
          border: '1px solid #1a4028',
          borderRadius: 'var(--radius)',
          fontSize: '13px',
          color: 'var(--state-converged-text)',
        }}>
          All clear — no gaps in this layer.
        </div>
      ) : (
        <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', width: '200px' }}>REQ Key</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Gap Type</th>
                {layer.gaps.some(g => g.files.length > 0) && (
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Files</th>
                )}
              </tr>
            </thead>
            <tbody>
              {layer.gaps.map((gap, i) => (
                <tr key={`${gap.req_key}-${i}`} style={{ borderBottom: i < layer.gaps.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <td style={{ padding: '10px 12px' }}><ReqLink reqKey={gap.req_key} localProjectId={projectId} /></td>
                  <td style={{ padding: '10px 12px', fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                    {gap.gap_type.replace('_', ' ')}
                  </td>
                  {layer.gaps.some(g => g.files.length > 0) && (
                    <td style={{ padding: '10px 12px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {gap.files.join(', ') || '—'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export function GapView({ projectId }: { projectId: string }) {
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['gaps', projectId],
    queryFn: () => api.getGaps(projectId),
  })

  if (isLoading) return <LoadingConsole messages={GAP_MESSAGES} label="gap analysis" />
  if (error) return <div style={{ padding: '16px', background: 'var(--stuck-bg)', border: '1px solid #4a1515', borderRadius: 'var(--radius)', color: 'var(--stuck-text)' }}>{String(error)}</div>
  if (!report) return null

  const totalGaps = (report.layer_1?.gap_count ?? 0) + (report.layer_2?.gap_count ?? 0)
  const healthColor = HEALTH_COLORS[report.health_signal] ?? '#6b7280'

  return (
    <div data-testid="gap-view">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: healthColor }} />
        <span style={{ fontWeight: 600, color: healthColor }}>{report.health_signal}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          {totalGaps} required gap{totalGaps !== 1 ? 's' : ''} (L1+L2) · L3 telemetry advisory
        </span>
      </div>

      {LAYER_META.map((meta) => {
        const layer = report[meta.key]
        if (!layer) return null
        return <LayerSection key={meta.key} meta={meta} layer={layer} pSlug={pSlug} />
      })}
    </div>
  )
}
