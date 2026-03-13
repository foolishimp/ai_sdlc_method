#!/usr/bin/env tsx
/**
 * e2e/eval.ts — Spec compliance evaluator
 *
 * Runs capture then prints instructions for Claude to evaluate the screenshot
 * against the page spec. Produces a structured delta report.
 *
 * Usage:
 *   npx tsx e2e/eval.ts --page overview
 *   npx tsx e2e/eval.ts --page feature-detail --feature REQ-F-FSNAV-001
 *   npx tsx e2e/eval.ts --all
 *
 * What it does:
 *   1. Captures screenshot(s) via capture.ts logic
 *   2. Reads the corresponding spec file
 *   3. Extracts the checklist items from the spec
 *   4. Prints screenshot path + checklist so Claude can evaluate visually
 *
 * Claude reads the screenshot image (Read tool) + the checklist and marks
 * each item pass/fail/unknown. Delta = count of failing required items.
 */

import { chromium, type Page } from '@playwright/test'
import * as path from 'node:path'
import * as fs from 'node:fs/promises'
import * as os from 'node:os'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const BASE_URL = process.env.VITE_APP_URL ?? 'http://localhost:5174'
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots')
const SPEC_ROOT = path.join(__dirname, '../../../specification/pages')
const VIEWPORT = { width: 1440, height: 900 }
const REGISTRY_FILE = path.join(os.homedir(), '.genesis_manager', 'workspaces.json')

// ─── Same page definitions as capture.ts ─────────────────────────────────────

const PAGES: Record<string, { url: (w: string, f?: string) => string; specFile: string; waitFor: string }> = {
  'project-list': {
    url: () => '/',
    specFile: 'PROJECT_LIST_PAGE.md',
    waitFor: 'main',
  },
  'overview': {
    url: (w) => `/project/${w}/overview`,
    specFile: 'OVERVIEW_PAGE.md',
    waitFor: 'header',
  },
  'supervision': {
    url: (w) => `/project/${w}/supervision`,
    specFile: 'SUPERVISION_PAGE.md',
    waitFor: 'header',
  },
  'evidence': {
    url: (w) => `/project/${w}/evidence`,
    specFile: 'EVIDENCE_PAGE.md',
    waitFor: 'header',
  },
  'feature-detail': {
    url: (w, f = 'REQ-F-FSNAV-001') => `/project/${w}/feature/${f}`,
    specFile: 'FEATURE_DETAIL_PAGE.md',
    waitFor: 'header',
  },
}

// ─── Extract checklist items from spec markdown ───────────────────────────────

function extractChecklist(specContent: string): string[] {
  const lines = specContent.split('\n')
  return lines
    .filter(l => l.trim().startsWith('- [ ]') || l.trim().startsWith('- [x]') || l.trim().startsWith('- [X]'))
    .map(l => l.trim())
}

// ─── Registry ─────────────────────────────────────────────────────────────────

async function getFirstWorkspaceId(): Promise<string> {
  const raw = await fs.readFile(REGISTRY_FILE, 'utf-8')
  const entries = JSON.parse(raw) as Array<{ id: string }>
  return entries[0].id
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2)
  const get = (flag: string) => { const i = args.indexOf(flag); return i !== -1 ? args[i + 1] : null }

  const pageName = get('--page')
  const featureId = get('--feature')
  const all = args.includes('--all')

  if (!pageName && !all) {
    console.error('Usage: npx tsx e2e/eval.ts --page <name> [--feature <id>] [--all]')
    console.error(`Pages: ${Object.keys(PAGES).join(', ')}`)
    process.exit(1)
  }

  const wsId = get('--workspace') ?? await getFirstWorkspaceId()
  const toEval = all ? Object.entries(PAGES) : [[pageName!, PAGES[pageName!]] as const]

  await fs.mkdir(SCREENSHOTS_DIR, { recursive: true })

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: VIEWPORT })
  const page = await context.newPage()
  page.on('console', () => {})
  page.on('pageerror', () => {})

  for (const [name, def] of toEval) {
    if (!def) { console.error(`Unknown page: ${name}`); continue }

    // ── 1. Capture screenshot ─────────────────────────────────────────────
    const screenshotPath = path.join(SCREENSHOTS_DIR, `${name}.png`)
    const url = `${BASE_URL}${def.url(wsId, featureId ?? undefined)}`

    console.log(`\n${'═'.repeat(60)}`)
    console.log(`PAGE: ${name}`)
    console.log(`URL:  ${url}`)

    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 })
    try { await page.waitForSelector(def.waitFor, { timeout: 5000 }) } catch { await page.waitForTimeout(2000) }
    await page.waitForTimeout(1500)
    await page.screenshot({ path: screenshotPath, fullPage: false })
    console.log(`SCREENSHOT: ${screenshotPath}`)

    // ── 2. Load spec and extract checklist ────────────────────────────────
    const specPath = path.join(SPEC_ROOT, def.specFile)
    let checklist: string[] = []
    let specExists = false

    try {
      const specContent = await fs.readFile(specPath, 'utf-8')
      checklist = extractChecklist(specContent)
      specExists = true
      console.log(`SPEC: ${specPath}`)
    } catch {
      console.log(`SPEC: NOT FOUND (${specPath})`)
    }

    // ── 3. Print evaluation prompt ────────────────────────────────────────
    console.log()
    console.log('── EVALUATION CHECKLIST ──')
    if (specExists && checklist.length > 0) {
      checklist.forEach((item, i) => console.log(`  ${i + 1}. ${item}`))
    } else if (specExists) {
      console.log('  (spec exists but has no checklist items — add "- [ ] ..." lines)')
    } else {
      console.log('  (no spec file — create specification/pages/' + def.specFile + ')')
    }

    console.log()
    console.log('── INSTRUCTIONS FOR EVALUATOR ──')
    console.log(`Read the screenshot at: ${screenshotPath}`)
    console.log('For each checklist item, mark: PASS / FAIL / CANNOT-TELL')
    console.log('DELTA = count of FAIL items on required checks')
    console.log('Report format:')
    console.log('  [PASS]  item text')
    console.log('  [FAIL]  item text  ← reason')
    console.log('  [?]     item text  ← what would be needed to verify')
    console.log()
  }

  await browser.close()
}

main().catch(err => { console.error(err); process.exit(1) })
