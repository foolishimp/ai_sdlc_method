import { useState, useEffect } from 'react'

interface LoadingConsoleProps {
  messages: string[]
  label: string
}

export function LoadingConsole({ messages, label }: LoadingConsoleProps) {
  const [elapsed, setElapsed] = useState(0)
  const [visibleLines, setVisibleLines] = useState(1)
  const [blink, setBlink] = useState(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(e => e + 100)
    }, 100)
    return () => clearInterval(timer)
  }, [])

  // Reveal one new message every 1.2 seconds
  useEffect(() => {
    if (visibleLines >= messages.length) return
    const timer = setTimeout(() => {
      setVisibleLines(v => v + 1)
    }, 1200)
    return () => clearTimeout(timer)
  }, [visibleLines, messages.length])

  // Blink cursor every 500ms
  useEffect(() => {
    const timer = setInterval(() => setBlink(b => !b), 500)
    return () => clearInterval(timer)
  }, [])

  const elapsedSec = (elapsed / 1000).toFixed(1)

  return (
    <div style={{
      background: '#0a0c10',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '0',
      overflow: 'hidden',
      fontFamily: 'var(--font-mono)',
    }}>
      {/* Terminal title bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '6px',
        padding: '8px 12px',
        background: 'var(--surface-2)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ff5f57' }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#febc2e' }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28c840' }} />
        <span style={{ marginLeft: 8, fontSize: '11px', color: 'var(--text-muted)' }}>
          genesis-nav — {label}
        </span>
        <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-muted)' }}>
          {elapsedSec}s
        </span>
      </div>

      {/* Console output */}
      <div style={{ padding: '16px', minHeight: '140px' }}>
        {messages.slice(0, visibleLines).map((msg, i) => (
          <div key={i} style={{ marginBottom: '6px', display: 'flex', gap: '8px' }}>
            <span style={{ color: '#4ade80', userSelect: 'none' }}>$</span>
            <span style={{ color: i < visibleLines - 1 ? '#8b949e' : '#e2e8f0' }}>{msg}</span>
            {i === visibleLines - 1 && i < messages.length - 1 && (
              <span style={{
                color: '#4ade80',
                opacity: blink ? 1 : 0,
                transition: 'opacity 0.1s',
              }}>▊</span>
            )}
          </div>
        ))}
        {visibleLines >= messages.length && (
          <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
            <span style={{ color: '#4ade80' }}>$</span>
            <span style={{ color: '#febc2e' }}>waiting for response</span>
            <span style={{
              color: '#4ade80',
              opacity: blink ? 1 : 0,
            }}>▊</span>
          </div>
        )}
      </div>
    </div>
  )
}
