// Implements: REQ-F-EVI-004
// Express Router for the gap-analysis rerun endpoint.
// POST /api/workspaces/:id/gap-analysis/rerun
// Spawns `gen-gaps` as a child process in the project root directory.
// Returns 202 immediately; stdout/stderr are streamed to the write_log.

import { Router, Request, Response } from 'express';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs/promises';
import os from 'node:os';
import { loadRegistry, findById } from '../lib/workspaceRegistry.js';

const router = Router();

const WRITE_LOG_FILE = path.join(os.homedir(), '.genesis_manager', 'write_log.jsonl');

async function appendToWriteLog(line: string): Promise<void> {
  try {
    await fs.mkdir(path.dirname(WRITE_LOG_FILE), { recursive: true });
    await fs.appendFile(WRITE_LOG_FILE, line + '\n', 'utf-8');
  } catch {
    // Best-effort
  }
}

// ---------------------------------------------------------------------------
// POST /api/workspaces/:id/gap-analysis/rerun
// Spawns gen-gaps in the project root (parent of .ai-workspace/).
// Returns 202 immediately; does not wait for completion.
// ---------------------------------------------------------------------------

router.post('/:id/gap-analysis/rerun', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;

  try {
    const registry = await loadRegistry();
    const reg = findById(id, registry);

    if (!reg) {
      res.status(404).json({ message: 'workspace not found' });
      return;
    }

    // Project root = parent of the registered .ai-workspace/ path
    const projectRoot = path.dirname(reg.path);

    const startedAt = new Date().toISOString();

    // Spawn gen-gaps detached from the request lifecycle
    const child = spawn('gen-gaps', [], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: false,
    });

    const logPrefix = JSON.stringify({
      timestamp: startedAt,
      action: 'gap_analysis_rerun',
      workspacePath: reg.path,
      pid: child.pid ?? null,
    });

    await appendToWriteLog(logPrefix);

    // Stream stdout / stderr to write_log (best-effort)
    child.stdout.on('data', (chunk: Buffer) => {
      const line = JSON.stringify({
        timestamp: new Date().toISOString(),
        action: 'gap_analysis_stdout',
        workspacePath: reg.path,
        data: chunk.toString('utf-8').trim(),
      });
      void appendToWriteLog(line);
    });

    child.stderr.on('data', (chunk: Buffer) => {
      const line = JSON.stringify({
        timestamp: new Date().toISOString(),
        action: 'gap_analysis_stderr',
        workspacePath: reg.path,
        data: chunk.toString('utf-8').trim(),
      });
      void appendToWriteLog(line);
    });

    child.on('close', (code) => {
      const line = JSON.stringify({
        timestamp: new Date().toISOString(),
        action: 'gap_analysis_complete',
        workspacePath: reg.path,
        exitCode: code,
      });
      void appendToWriteLog(line);
    });

    child.on('error', (err) => {
      const line = JSON.stringify({
        timestamp: new Date().toISOString(),
        action: 'gap_analysis_error',
        workspacePath: reg.path,
        error: String(err),
      });
      void appendToWriteLog(line);
    });

    // Return 202 immediately — client polls for the gaps_validated event
    res.status(202).json({
      message: 'gen-gaps started',
      startedAt,
      pid: child.pid ?? null,
    });
  } catch (err) {
    console.error('[POST /gap-analysis/rerun]', err);
    res.status(500).json({ message: 'Failed to start gen-gaps' });
  }
});

export default router;
