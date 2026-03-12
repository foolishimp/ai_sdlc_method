// Implements: ADR-GM-002
// Express server entry point — bridges the browser-filesystem gap.
// Mounts all route modules under /api and serves the static Vite build in
// production (NODE_ENV=production).

import 'dotenv/config';
import express, {
  type Request,
  type Response,
  type NextFunction,
} from 'express';
import cors from 'cors';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import workspacesRouter from './routes/workspaces.js';
import workspaceRouter from './routes/workspace.js';
import eventsRouter from './routes/events.js';
import gapAnalysisRouter from './routes/gapAnalysis.js';
import navRouter from './routes/nav.js';
import fsRouter from './routes/fs.js';

// ---------------------------------------------------------------------------
// ESM __dirname shim
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// App setup
// ---------------------------------------------------------------------------

const app = express();

// CORS — allow the Vite dev server origin in development
app.use(
  cors({
    origin:
      process.env['NODE_ENV'] === 'production'
        ? false
        : ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:5174', 'http://127.0.0.1:5174'],
    methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type'],
  }),
);

// JSON body parser (max 1 MB — events are small payloads)
app.use(express.json({ limit: '1mb' }));

// ---------------------------------------------------------------------------
// API routes
// ---------------------------------------------------------------------------

// Workspace registration: GET/POST/DELETE /api/workspaces
app.use('/api/workspaces', workspacesRouter);

// Workspace detail: GET /api/workspaces/:id/overview|gates|features|traceability
app.use('/api/workspaces', workspaceRouter);

// Event write path: POST /api/workspaces/:id/events
app.use('/api/workspaces', eventsRouter);

// Gap analysis rerun: POST /api/workspaces/:id/gap-analysis/rerun
app.use('/api/workspaces', gapAnalysisRouter);

// Navigation resolution: GET /api/features/:id, /api/req/:key, /api/events/:index
app.use('/api', navRouter);

// Filesystem browse: GET /api/fs/browse?path=<dir>
// Implements: REQ-F-FSNAV-001
app.use('/api/fs', fsRouter);

// ---------------------------------------------------------------------------
// Static SPA serving (production only)
// ---------------------------------------------------------------------------

if (process.env['NODE_ENV'] === 'production') {
  const distPath = path.join(__dirname, '..', 'dist');
  app.use(express.static(distPath));

  // Fallback: serve index.html for any non-API path (SPA client-side routing)
  app.get('*', (_req: Request, res: Response) => {
    res.sendFile(path.join(distPath, 'index.html'));
  });
}

// ---------------------------------------------------------------------------
// Global error handler
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[Unhandled error]', err);
  res.status(500).json({ message: 'Internal server error' });
});

// ---------------------------------------------------------------------------
// Server startup
// ---------------------------------------------------------------------------

export function startServer(port: number = 3001): void {
  app.listen(port, () => {
    console.log(`[genesis-manager] API server listening on http://localhost:${port}`);
    console.log(`[genesis-manager] ENV: ${process.env['NODE_ENV'] ?? 'development'}`);
  });
}

const port = parseInt(process.env['PORT'] ?? '3001', 10);
startServer(port);
