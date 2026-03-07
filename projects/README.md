# Projects

Downstream projects **built using** the Genesis methodology. Distinct from `imp_*/` which implement the methodology for LLM platforms.

Each project here:
- Is a self-contained Genesis sub-project with its own `specification/`, `CLAUDE.md`, and `.ai-workspace/`
- Is dogfooding the methodology — its own construction is an instance of Genesis executing
- Consumes or extends the methodology's outputs (events.jsonl, workspaces, event streams) rather than defining them

## Projects

| Project | Role | Interface |
|---------|------|-----------|
| [`genesis_monitor/`](genesis_monitor/) | Real-time observer dashboard | Consumes `events.jsonl` (OpenLineage) |
| [`eco_system/`](eco_system/) | Validation ecosystem — reference projects, snapshots, prove edges | Produces `events.jsonl`; resettable to named checkpoints |

## Relationship

```
eco_system/          ← executes Genesis on reference projects → produces events.jsonl
                                                                        ↓
genesis_monitor/     ← consumes events.jsonl → visualises convergence, H, phase space
```

The two projects close the observer loop: the ecosystem generates the event stream that proves the methodology; the monitor makes that stream visible in real time.

## Adding a New Project

Any project that builds against the Genesis methodology's outputs belongs here. It should have:

```
projects/<name>/
├── specification/INTENT.md     ← why this project exists
├── imp_<tech>/                 ← implementation (one per technology)
│   ├── CLAUDE.md               ← Genesis bootloader
│   ├── design/adrs/
│   ├── code/
│   ├── tests/
│   └── .ai-workspace/          ← this sub-project's Genesis workspace
└── README.md
```
