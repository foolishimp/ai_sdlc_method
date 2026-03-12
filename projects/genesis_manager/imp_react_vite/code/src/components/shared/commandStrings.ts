// Implements: REQ-F-UX-002
// CMD — maps action type to genesis command string equivalent.
// All values are informational labels; the user never needs to type them.

export const CMD = {
  startIteration: (featureId: string, edge?: string): string =>
    edge
      ? `gen-start --feature ${featureId} --edge ${edge}`
      : `gen-start --feature ${featureId}`,

  approveGate: (featureId: string, edge: string, gateName?: string): string =>
    gateName
      ? `gen-review --feature ${featureId} --gate ${gateName} --decision approved`
      : `gen-review --feature ${featureId} --edge ${edge} --decision approved`,

  rejectGate: (featureId: string, edge: string, comment: string, gateName?: string): string =>
    gateName
      ? `gen-review --feature ${featureId} --gate ${gateName} --decision rejected --comment "${comment}"`
      : `gen-review --feature ${featureId} --edge ${edge} --decision rejected --comment "${comment}"`,

  spawnFeature: (parentId: string, type: string, reason: string): string =>
    `gen-spawn --type ${type} --parent ${parentId} --reason "${reason}"`,

  setAutoMode: (featureId: string, enabled: boolean): string =>
    enabled
      ? `gen-auto --feature ${featureId} --enable`
      : `gen-auto --feature ${featureId} --disable`,

  rerunGaps: (): string => 'gen-gaps',

  release: (): string => 'gen-release',
} as const
