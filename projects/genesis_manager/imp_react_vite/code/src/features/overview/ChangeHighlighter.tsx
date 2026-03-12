// Implements: REQ-F-OVR-004

import React, { createContext, useContext, useCallback, useState } from 'react'

const SESSION_KEY = 'gm:lastSessionStart'

interface ChangeContextValue {
  lastSessionStart: Date | null
  isChanged: (featureId: string, featureLastEventAt: string | undefined) => boolean
  dismissChanges: () => void
}

const ChangeContext = createContext<ChangeContextValue>({
  lastSessionStart: null,
  isChanged: () => false,
  dismissChanges: () => undefined,
})

// ChangeHighlighter — React context provider for session-based change detection.
// Wraps the overview page tree; exposes isChanged() and dismissChanges().
// Implements: REQ-F-OVR-004
export function ChangeHighlighterProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  // Read the previous session's start timestamp from localStorage on mount.
  // That value IS lastSessionStart — it was written by the previous session.
  const [lastSessionStart, setLastSessionStart] = useState<Date | null>(() => {
    const stored = localStorage.getItem(SESSION_KEY)
    if (!stored) {
      // First visit — write now, nothing is "new"
      localStorage.setItem(SESSION_KEY, new Date().toISOString())
      return null
    }
    return new Date(stored)
  })

  // isChanged — returns true if the feature has activity after lastSessionStart.
  const isChanged = useCallback(
    (featureId: string, featureLastEventAt: string | undefined): boolean => {
      if (!lastSessionStart || !featureLastEventAt) return false
      void featureId // featureId used for hook identity; actual comparison uses timestamp
      return new Date(featureLastEventAt) > lastSessionStart
    },
    [lastSessionStart],
  )

  // dismissChanges — write current timestamp; all items become "seen".
  // Implements: REQ-F-OVR-004 AC3
  const dismissChanges = useCallback(() => {
    const now = new Date()
    localStorage.setItem(SESSION_KEY, now.toISOString())
    setLastSessionStart(now)
  }, [])

  return (
    <ChangeContext.Provider value={{ lastSessionStart, isChanged, dismissChanges }}>
      {children}
    </ChangeContext.Provider>
  )
}

export function useChangeHighlighter(): ChangeContextValue {
  return useContext(ChangeContext)
}

// ChangeBadge — inline "NEW" badge for changed items.
export function ChangeBadge(): React.JSX.Element {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700 ml-1">
      NEW
    </span>
  )
}
