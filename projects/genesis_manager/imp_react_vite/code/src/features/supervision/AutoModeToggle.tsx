// Implements: REQ-F-CTL-004, REQ-BR-SUPV-001

import React, { useState } from 'react'
import { apiClient } from '../../api/WorkspaceApiClient'
import { ConfirmActionDialog } from '../../components/shared/ConfirmActionDialog'
import { CMD } from '../../components/shared/commandStrings'

interface AutoModeToggleProps {
  workspaceId: string
  featureId: string
  // Derived from most recent auto_mode_set event (REQ-DATA-WORK-001)
  currentlyEnabled: boolean
  onComplete: () => void
}

// AutoModeToggle — visible in every feature row so the user can always see and disable it.
// Derives state from events, never from hidden config.
// Implements: REQ-F-CTL-004, REQ-BR-SUPV-001
export function AutoModeToggle({
  workspaceId,
  featureId,
  currentlyEnabled,
  onComplete,
}: AutoModeToggleProps): React.JSX.Element {
  const [dialogOpen, setDialogOpen] = useState(false)

  const handleToggle = async () => {
    if (currentlyEnabled) {
      // Turning OFF — no dialog needed, non-destructive
      await apiClient.setAutoMode(workspaceId, featureId, false)
      onComplete()
    } else {
      // Turning ON — require confirmation with warning
      setDialogOpen(true)
    }
  }

  const handleConfirmEnable = async () => {
    await apiClient.setAutoMode(workspaceId, featureId, true)
    setDialogOpen(false)
    onComplete()
  }

  return (
    <>
      <button
        onClick={() => void handleToggle()}
        role="switch"
        aria-checked={currentlyEnabled}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
          currentlyEnabled ? 'bg-primary' : 'bg-muted'
        }`}
        title={CMD.setAutoMode(featureId, !currentlyEnabled)}
      >
        <span
          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-secondary shadow transition-transform ${
            currentlyEnabled ? 'translate-x-4' : 'translate-x-0.5'
          }`}
        />
      </button>

      <ConfirmActionDialog
        open={dialogOpen}
        title="Enable Auto Mode"
        description={`Enable auto-mode for feature ${featureId}?`}
        command={CMD.setAutoMode(featureId, true)}
        warningMessage="Auto-mode will continuously iterate until a human gate is reached. You can disable it at any time."
        onConfirm={handleConfirmEnable}
        onCancel={() => setDialogOpen(false)}
      />
    </>
  )
}
