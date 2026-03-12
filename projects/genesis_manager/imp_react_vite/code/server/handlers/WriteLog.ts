// Implements: REQ-DATA-WORK-002
// Appends a structured write-log entry to ~/.genesis_manager/write_log.jsonl
// Called after every successful write to events.jsonl to satisfy the audit requirement.

import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GENESIS_MANAGER_DIR = path.join(os.homedir(), '.genesis_manager');
const WRITE_LOG_FILE = path.join(GENESIS_MANAGER_DIR, 'write_log.jsonl');

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WriteLogEntry {
  timestamp: string;
  action: string;
  workspacePath: string;
  eventType?: string;
  actor?: string;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Append a single JSONL entry to the write log.
 * Best-effort — errors are logged to stderr but not thrown to the caller.
 * The write log is an audit trail; failure to write it must not block the
 * primary write operation.
 */
export async function appendWriteLog(entry: WriteLogEntry): Promise<void> {
  try {
    await fs.mkdir(GENESIS_MANAGER_DIR, { recursive: true });
    const line = JSON.stringify(entry) + '\n';
    await fs.appendFile(WRITE_LOG_FILE, line, 'utf-8');
  } catch (err) {
    // Non-fatal: log to stderr and continue
    console.error('[WriteLog] Failed to append write log entry:', err);
  }
}
