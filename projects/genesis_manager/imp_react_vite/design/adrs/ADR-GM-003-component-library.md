# ADR-GM-003: Component Library — Tailwind CSS + shadcn/ui
# Implements: Cross-cutting component design system (design_recommendations §Cross-Cutting: Component Design System)

**Status**: Accepted | **Date**: 2026-03-13

## Context
All 7 MVP features share UI primitives: status badges, navigation handle chips, gate queue items, freshness indicators. A shared component design system must be chosen before Phase 3 features begin (OVR, SUP, EVI all use these primitives).

## Decision
**Tailwind CSS** for styling + **shadcn/ui** for headless component primitives (Button, Badge, Drawer, Dialog, Form).

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Tailwind + shadcn/ui** | shadcn/ui components are owned (copied to project, not an npm dependency); TypeScript-first; accessible by default; Vite + React compatible; small bundle | Requires careful copy discipline; not a drop-in library |
| **Material UI (MUI)** | Large component set; mature ecosystem | Heavy bundle; opinionated styling hard to override; v5 Emotion CSS-in-JS adds complexity with Vite |
| **Custom CSS modules** | Full control; zero dependency | High implementation cost for a supervision console with complex component requirements |

## Consequences
- `npx shadcn@latest init` generates `src/components/ui/` with owned component copies
- Shared primitives: `StatusBadge`, `NavHandle`, `FreshnessIndicator`, `GateQueueItem` built on top of shadcn/ui Badge + Button
- All feature-specific components import from `src/components/ui/` — no direct shadcn imports in features
- **Connects to**: All Phase 2–4 features consume the shared component system
