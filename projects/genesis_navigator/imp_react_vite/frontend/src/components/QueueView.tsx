// Implements: REQ-F-QUEUE-001, REQ-F-QUEUE-002, REQ-F-QUEUE-003
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { LoadingConsole } from './LoadingConsole'
import type { QueueItem } from '../api/types'
import { ReqLink } from './ui/ReqLink'

const QUEUE_MESSAGES = [
  'Reading .ai-workspace/events/events.jsonl',
  'Computing Hamiltonian H=T+V per feature',
  'Detecting stuck deltas (δ unchanged 3+ iterations)',
  'Resolving blocked dependencies',
  'Scanning gap clusters from traceability analysis',
  'Ranking work items by priority',
]

const TYPE_CONFIG: Record<string, { bg: string; text: string }> = {
  STUCK:       { bg: 'var(--stuck-bg)',    text: 'var(--stuck-text)' },
  BLOCKED:     { bg: 'var(--blocked-bg)',  text: 'var(--blocked-text)' },
  GAP_CLUSTER: { bg: 'var(--gap-bg)',      text: 'var(--gap-text)' },
  IN_PROGRESS: { bg: 'var(--progress-bg)', text: 'var(--progress-text)' },
}

const SEV_COLORS: Record<string, string> = {
  high: 'var(--stuck-text)', medium: 'var(--blocked-text)', low: 'var(--text-muted)',
}

function QueueCard({ item, pSlug }: { item: QueueItem; pSlug: string }) {
  const tc = TYPE_CONFIG[item.type] ?? { bg: 'var(--surface-2)', text: 'var(--text-secondary)' }
  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      marginBottom: '8px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{
          padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700,
          letterSpacing: '0.04em', backgroundColor: tc.bg, color: tc.text,
        }}>
          {item.type.replace('_', ' ')}
        </span>
        <span style={{ fontSize: '11px', fontWeight: 600, color: SEV_COLORS[item.severity] ?? 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {item.severity}
        </span>
        {item.feature_id && (
          <ReqLink reqKey={item.feature_id} localProjectId={projectId} style={{ color: 'var(--text-secondary)' }} />
        )}
        {item.detail.delta !== null && (
          <span style={{ marginLeft: 'auto', fontSize: '18px', fontWeight: 700, color: item.detail.delta > 0 ? 'var(--stuck-text)' : 'var(--state-converged-text)' }}>
            δ{item.detail.delta}
          </span>
        )}
      </div>

      <div style={{ fontSize: '13px', marginBottom: '6px' }}>{item.description}</div>
      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>{item.detail.reason}</div>

      {item.detail.gap_keys.length > 0 && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {item.detail.gap_keys.slice(0, 6).map((k, i) => (
            <span key={k}>{i > 0 && ' · '}<ReqLink reqKey={k} localProjectId={projectId} style={{ fontSize: '11px' }} /></span>
          ))}
          {item.detail.gap_keys.length > 6 && ` +${item.detail.gap_keys.length - 6}`}
        </div>
      )}

      {item.detail.failing_checks.length > 0 && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Failing: {item.detail.failing_checks.join(', ')}
        </div>
      )}

      <div style={{ marginTop: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--accent)', opacity: 0.7 }}>
        {item.command}
      </div>
    </div>
  )
}

export function QueueView({ projectId }: { projectId: string }) {
  const { data: items, isLoading, error } = useQuery({
    queryKey: ['queue', projectId],
    queryFn: () => api.getQueue(projectId),
  })

  if (isLoading) return <LoadingConsole messages={QUEUE_MESSAGES} label="queue builder" />
  if (error) return (
    <div style={{ padding: '16px', background: 'var(--stuck-bg)', border: '1px solid #4a1515', borderRadius: 'var(--radius)', color: 'var(--stuck-text)' }}>
      {String(error)}
    </div>
  )

  const queue = items ?? []

  return (
    <div data-testid="queue-view">
      {queue.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '64px 0',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>✓</div>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>Queue is empty</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Nothing needs attention right now.</div>
        </div>
      ) : (
        <>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            {queue.length} item{queue.length !== 1 ? 's' : ''} need attention
          </div>
          {queue.map((item, i) => <QueueCard key={`${item.type}-${item.feature_id ?? ''}-${i}`} item={item} pSlug={pSlug} />)}
        </>
      )}
    </div>
  )
}
