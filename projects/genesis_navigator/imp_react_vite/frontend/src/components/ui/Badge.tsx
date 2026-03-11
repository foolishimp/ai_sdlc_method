const STATE_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  ITERATING:     { label: 'Iterating',     bg: 'var(--state-iterating-bg)',     text: 'var(--state-iterating-text)',     dot: 'var(--state-iterating-dot)' },
  CONVERGED:     { label: 'Converged',     bg: 'var(--state-converged-bg)',     text: 'var(--state-converged-text)',     dot: 'var(--state-converged-dot)' },
  QUIESCENT:     { label: 'Quiescent',     bg: 'var(--state-quiescent-bg)',     text: 'var(--state-quiescent-text)',     dot: 'var(--state-quiescent-dot)' },
  BOUNDED:       { label: 'Bounded',       bg: 'var(--state-bounded-bg)',       text: 'var(--state-bounded-text)',       dot: 'var(--state-bounded-dot)' },
  UNINITIALIZED: { label: 'Uninitialised', bg: 'var(--state-uninitialized-bg)', text: 'var(--state-uninitialized-text)', dot: 'var(--state-uninitialized-dot)' },
}

export function StateBadge({ state }: { state: string }) {
  const cfg = STATE_CONFIG[state] ?? STATE_CONFIG.UNINITIALIZED
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '2px 8px', borderRadius: '100px',
      backgroundColor: cfg.bg, color: cfg.text,
      fontSize: '11px', fontWeight: 600, letterSpacing: '0.02em',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: cfg.dot, flexShrink: 0 }} />
      {cfg.label}
    </span>
  )
}

const QUEUE_CONFIG: Record<string, { bg: string; text: string }> = {
  STUCK:       { bg: 'var(--stuck-bg)',    text: 'var(--stuck-text)' },
  BLOCKED:     { bg: 'var(--blocked-bg)',  text: 'var(--blocked-text)' },
  GAP_CLUSTER: { bg: 'var(--gap-bg)',      text: 'var(--gap-text)' },
  IN_PROGRESS: { bg: 'var(--progress-bg)', text: 'var(--progress-text)' },
}

export function QueueTypeBadge({ type }: { type: string }) {
  const cfg = QUEUE_CONFIG[type] ?? { bg: 'var(--surface-2)', text: 'var(--text-secondary)' }
  return (
    <span style={{
      display: 'inline-block', padding: '1px 7px',
      borderRadius: '4px', backgroundColor: cfg.bg, color: cfg.text,
      fontSize: '11px', fontWeight: 700, letterSpacing: '0.04em',
    }}>
      {type.replace('_', ' ')}
    </span>
  )
}

const SEVERITY_COLORS: Record<string, string> = {
  high: '#dc2626', medium: '#d97706', low: '#6b7280',
}

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span style={{ color: SEVERITY_COLORS[severity] ?? '#6b7280', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
      {severity}
    </span>
  )
}
