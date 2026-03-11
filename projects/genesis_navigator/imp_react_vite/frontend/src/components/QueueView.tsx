// Implements: REQ-F-QUEUE-001, REQ-F-QUEUE-002, REQ-F-QUEUE-003
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { QueueItem } from '../api/types'

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  STUCK: { bg: '#fee2e2', text: '#991b1b' },
  BLOCKED: { bg: '#fef3c7', text: '#92400e' },
  GAP_CLUSTER: { bg: '#ede9fe', text: '#5b21b6' },
  IN_PROGRESS: { bg: '#dbeafe', text: '#1e40af' },
}

function QueueCard({ item }: { item: QueueItem }) {
  const colors = TYPE_COLORS[item.item_type] ?? { bg: '#f3f4f6', text: '#374151' }
  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold', backgroundColor: colors.bg, color: colors.text }}>
            {item.item_type}
          </span>
          <span style={{ fontWeight: 'bold', fontSize: '0.875rem' }}>{item.feature_id}</span>
        </div>
        {item.delta !== null && (
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>δ={item.delta}</span>
        )}
      </div>
      <div style={{ fontSize: '0.875rem', marginBottom: '4px' }}>{item.title}</div>
      <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '4px' }}>{item.description}</div>
      {item.edge && <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Edge: {item.edge}</div>}
      {item.blocked_by && <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>Blocked by: {item.blocked_by}</div>}
      {item.consecutive_failures > 0 && (
        <div style={{ fontSize: '0.75rem', color: '#d97706' }}>Consecutive failures: {item.consecutive_failures}</div>
      )}
      {item.affected_req_keys.length > 0 && (
        <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '4px' }}>
          {item.affected_req_keys.slice(0, 5).join(', ')}{item.affected_req_keys.length > 5 ? ` +${item.affected_req_keys.length - 5} more` : ''}
        </div>
      )}
    </div>
  )
}

export function QueueView({ projectId }: { projectId: string }) {
  const { data: items, isLoading, error } = useQuery({
    queryKey: ['queue', projectId],
    queryFn: () => api.getQueue(projectId),
  })

  if (isLoading) return <div>Loading queue…</div>
  if (error) return <div style={{ color: '#dc2626' }}>Error: {String(error)}</div>

  const queue = items ?? []

  return (
    <div data-testid="queue-view">
      {queue.length === 0 ? (
        <p style={{ color: '#6b7280' }}>Queue is empty — nothing needs attention.</p>
      ) : (
        <>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '16px' }}>
            {queue.length} item{queue.length !== 1 ? 's' : ''} need attention (ranked by priority)
          </p>
          {queue.map((item, i) => (
            <QueueCard key={`${item.feature_id}-${i}`} item={item} />
          ))}
        </>
      )}
    </div>
  )
}
