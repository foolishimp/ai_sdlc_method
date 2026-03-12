// Implements: REQ-F-UX-001

import React, { useEffect, useState } from 'react'

interface FreshnessIndicatorProps {
  lastRefreshed: Date | null
  isRefreshing: boolean
  error: string | null
  className?: string
}

// FreshnessIndicator — 5-state machine showing data freshness.
// States: loading | refreshing | fresh | stale | error
// Implements: REQ-F-UX-001
export function FreshnessIndicator({
  lastRefreshed,
  isRefreshing,
  error,
  className,
}: FreshnessIndicatorProps): React.JSX.Element {
  const [now, setNow] = useState(() => Date.now())

  // Update the displayed age every 5 seconds
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 5_000)
    return () => clearInterval(id)
  }, [])

  const base = `inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${className ?? ''}`

  // State: refreshing
  if (isRefreshing) {
    return (
      <span className={`${base} bg-blue-50 text-blue-700`}>
        <span className="animate-spin inline-block w-3 h-3 border border-blue-500 border-t-transparent rounded-full" />
        Refreshing…
      </span>
    )
  }

  // State: error
  if (error) {
    return (
      <span className={`${base} bg-red-50 text-red-700`}>
        <span className="w-2 h-2 rounded-full bg-red-500" />
        Workspace unavailable: {error}
      </span>
    )
  }

  // State: loading (never refreshed)
  if (!lastRefreshed) {
    return (
      <span className={`${base} bg-gray-100 text-gray-500`}>
        <span className="w-2 h-2 rounded-full bg-gray-400" />
        Loading…
      </span>
    )
  }

  const ageMs = now - lastRefreshed.getTime()
  const ageSec = Math.round(ageMs / 1000)
  const stale = ageMs > 60_000

  // State: stale (>60s)
  if (stale) {
    return (
      <span className={`${base} bg-red-50 text-red-700`}>
        <span className="w-2 h-2 rounded-full bg-red-500" />
        Last refreshed {ageSec}s ago — stale
      </span>
    )
  }

  // State: fresh
  return (
    <span className={`${base} bg-green-50 text-green-700`}>
      <span className="w-2 h-2 rounded-full bg-green-500" />
      Last refreshed {ageSec}s ago
    </span>
  )
}
