// Implements: REQ-F-HIST-001
// Implements: REQ-F-HIST-002
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { LoadingConsole } from './LoadingConsole'
import type { RunSummary, RunTimeline, RunSegment, RunEvent } from '../api/types'

// ---------------------------------------------------------------------------
// Event type visual config
// ---------------------------------------------------------------------------

const EVENT_TYPE_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  edge_started:          { color: '#1d4ed8', bg: '#dbeafe', label: 'edge_started' },
  iteration_completed:   { color: '#92400e', bg: '#fef3c7', label: 'iteration_completed' },
  edge_converged:        { color: '#15803d', bg: '#dcfce7', label: 'edge_converged' },
  intent_raised:         { color: '#7c3aed', bg: '#ede9fe', label: 'intent_raised' },
  project_initialized:   { color: '#0e7490', bg: '#cffafe', label: 'project_initialized' },
  health_checked:        { color: '#6b7280', bg: '#f3f4f6', label: 'health_checked' },
  gaps_validated:        { color: '#0369a1', bg: '#e0f2fe', label: 'gaps_validated' },
}

function eventConfig(type: string) {
  return EVENT_TYPE_CONFIG[type] ?? { color: '#6b7280', bg: '#f3f4f6', label: type }
}

const FINAL_STATE_CONFIG: Record<string, { color: string; bg: string }> = {
  CONVERGED:    { color: '#15803d', bg: '#dcfce7' },
  ITERATING:    { color: '#1d4ed8', bg: '#dbeafe' },
  UNINITIALIZED:{ color: '#6b7280', bg: '#f3f4f6' },
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function EventTypeBadge({ type }: { type: string }) {
  const cfg = eventConfig(type)
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 7px',
      borderRadius: '4px',
      background: cfg.bg,
      color: cfg.color,
      fontSize: '11px',
      fontWeight: 600,
      fontFamily: 'var(--font-mono)',
      whiteSpace: 'nowrap',
    }}>
      {cfg.label}
    </span>
  )
}

function FinalStateBadge({ state }: { state: string }) {
  const cfg = FINAL_STATE_CONFIG[state] ?? { color: '#6b7280', bg: '#f3f4f6' }
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 7px',
      borderRadius: '4px',
      background: cfg.bg,
      color: cfg.color,
      fontSize: '11px',
      fontWeight: 600,
      fontFamily: 'var(--font-mono)',
    }}>
      {state}
    </span>
  )
}

function RunCard({ run, selected, onClick }: { run: RunSummary; selected: boolean; onClick: () => void }) {
  const ts = run.timestamp ? new Date(run.timestamp).toLocaleString() : '—'
  return (
    <button
      data-testid={`run-card-${run.run_id}`}
      onClick={onClick}
      style={{
        width: '100%',
        textAlign: 'left',
        padding: '12px 14px',
        background: selected ? 'var(--accent-subtle, #eff6ff)' : 'var(--surface)',
        border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 'var(--radius)',
        marginBottom: '6px',
        cursor: 'pointer',
        transition: 'border-color 0.1s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
          {run.is_current ? '● Current Session' : run.run_id}
        </span>
        <FinalStateBadge state={run.final_state} />
      </div>
      <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
        <span>{run.event_count} events</span>
        <span>{run.edges_traversed} edges</span>
        <span title={run.timestamp ?? undefined}>{ts}</span>
      </div>
    </button>
  )
}

function EventRow({ event }: { event: RunEvent }) {
  const ts = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : null
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      padding: '5px 0',
      borderBottom: '1px solid var(--border)',
      fontSize: '12px',
    }}>
      <EventTypeBadge type={event.event_type} />
      {ts && (
        <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap', flexShrink: 0, paddingTop: '1px' }}>
          {ts}
        </span>
      )}
    </div>
  )
}

function SegmentBlock({ segment }: { segment: RunSegment }) {
  const header = segment.feature
    ? `${segment.feature}${segment.edge ? ` · ${segment.edge}` : ''}`
    : '(project)'
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{
        fontSize: '11px',
        fontFamily: 'var(--font-mono)',
        fontWeight: 600,
        color: 'var(--text-secondary)',
        marginBottom: '6px',
        padding: '4px 8px',
        background: 'var(--surface-2, #f8fafc)',
        borderRadius: '4px',
        borderLeft: '3px solid var(--accent)',
      }}>
        {header}
        <span style={{ fontWeight: 400, marginLeft: '8px', color: 'var(--text-muted)' }}>
          {segment.events.length} event{segment.events.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div style={{ paddingLeft: '8px' }}>
        {segment.events.map((ev, i) => (
          <EventRow key={i} event={ev} />
        ))}
      </div>
    </div>
  )
}

function TimelinePanel({ projectId, runId }: { projectId: string; runId: string }) {
  const { data, isLoading, error } = useQuery<RunTimeline>({
    queryKey: ['run-timeline', projectId, runId],
    queryFn: () => api.getRunTimeline(projectId, runId),
    enabled: !!runId,
  })

  if (isLoading) {
    return (
      <LoadingConsole
        label={`loading timeline for ${runId}`}
        messages={[
          'reading events.jsonl',
          'grouping by feature + edge',
          'building timeline segments',
        ]}
      />
    )
  }
  if (error) {
    return (
      <div style={{ padding: '16px', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', color: '#991b1b', fontSize: '13px' }}>
        {String(error)}
      </div>
    )
  }
  if (!data) return null

  return (
    <div data-testid="timeline-panel">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 600 }}>
          {runId === 'current' ? 'Current Session' : runId}
        </span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{data.event_count} events total</span>
      </div>

      {data.segments.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px 0', fontSize: '13px' }}>
          No events in this run.
        </div>
      ) : (
        data.segments.map((seg, i) => (
          <SegmentBlock key={i} segment={seg} />
        ))
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export function HistoryView({ projectId }: { projectId: string }) {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)

  const { data: runs, isLoading, error } = useQuery<RunSummary[]>({
    queryKey: ['runs', projectId],
    queryFn: () => api.listRuns(projectId),
    enabled: !!projectId,
  })

  if (isLoading) {
    return (
      <LoadingConsole
        label="loading run history"
        messages={[
          'scanning workspace events',
          'discovering archived e2e runs',
          'computing run summaries',
        ]}
      />
    )
  }

  if (error) {
    return (
      <div style={{ padding: '16px', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', color: '#991b1b', fontSize: '13px' }}>
        {String(error)}
      </div>
    )
  }

  const runList = runs ?? []
  const active = selectedRunId ?? (runList.length > 0 ? runList[0].run_id : null)

  return (
    <div data-testid="history-view" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', alignItems: 'start' }}>
      {/* Run list */}
      <div>
        <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
          Runs
        </div>
        {runList.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px 0', fontSize: '13px' }}>
            No runs found.
          </div>
        ) : (
          runList.map((run) => (
            <RunCard
              key={run.run_id}
              run={run}
              selected={run.run_id === active}
              onClick={() => setSelectedRunId(run.run_id)}
            />
          ))
        )}
      </div>

      {/* Timeline */}
      <div>
        <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
          Event Timeline
        </div>
        {active ? (
          <TimelinePanel projectId={projectId} runId={active} />
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '48px 0', fontSize: '13px' }}>
            Select a run to view its event timeline.
          </div>
        )}
      </div>
    </div>
  )
}
