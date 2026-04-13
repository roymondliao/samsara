[中文版 README](./README.zh-TW.md)

# Samsara (向死而驗)

> Toward death, through verification.

Samsara is a [Claude Code plugin](https://code.claude.com/docs/en/plugins) that enforces a death-first development workflow. Instead of asking "does it work?", Samsara asks "when it breaks silently, who will know?"

Every function, module, and design decision must answer: **"If you disappeared, what would feel the pain?"** If it can't answer, it shouldn't exist.

## Philosophy

Traditional development follows the yang side — build features, verify they work, ship. Samsara inverts this by leading with the **yin side**: identify where things can silently fail, rot without warning, or degrade while pretending to be healthy.

This manifests in three core principles:

1. **Death tests before unit tests** — Test how things fail silently before testing how they succeed
2. **Scar reports before completion** — Every implementation must name its wounds: assumptions, silent failure paths, edge cases
3. **STEP 0 before any implementation** — Three mandatory questions that prevent confirmation bias:
   - What is the most obvious implementation? Don't take that path yet.
   - Under what conditions should this not be implemented at all?
   - If this silently fails, who discovers it first? How far has the damage spread?

## Installation

Samsara is a Claude Code plugin. Add it to your project:

```bash
# In your project's .claude/settings.json
{
  "plugins": {
    "samsara": true
  }
}
```

Or install from a local path:

```bash
claude plugins add /path/to/samsara
```

Once installed, Samsara injects its axioms and constraints at session start via a `SessionStart` hook.

## Workflow

Samsara provides a structured workflow from research to shipping. Each phase produces specific artifacts that feed into the next.

```
research  ──>  planning  ──>  implement  ──>  validate-and-ship
                                  ^
                                  │
fast-track (small changes) ───────┘
debugging (production failures) ──┘
```

### Skills

| Skill | When to use | Key output |
|-------|-------------|------------|
| `samsara:research` | Starting new feature work or investigating a problem | Kickoff doc + problem autopsy |
| `samsara:planning` | After research is complete | Death-first spec + tasks with acceptance criteria |
| `samsara:implement` | Plan with tasks is ready | Code with death tests + scar reports |
| `samsara:validate-and-ship` | All tasks complete | Ship manifest with failure budget |
| `samsara:fast-track` | Small, low-risk changes (< 100 lines) | Compressed workflow, death test still first |
| `samsara:debugging` | Production failure in existing code | Four-phase yin-side root cause analysis |
| `samsara:codebase-map` | Entering a new project or after significant changes | Structural map + silent failure surface assessment |
| `samsara:writing-skills` | Creating or modifying samsara skills | Death-first TDD applied to skill development |

### Agents

Samsara includes specialized subagents that carry yin-side constraints in their definitions — they don't rely on prompt injection to maintain the framework's spirit.

| Agent | Purpose | Model |
|-------|---------|-------|
| `samsara:implementer` | Death-test-first implementation with scar reports | sonnet |
| `samsara:code-reviewer` | Yin-side code review: deletion before correctness, naming honesty, silent rot paths | sonnet |
| `samsara:structure-explorer` | Map module boundaries, dependencies, public interfaces | sonnet |
| `samsara:infra-explorer` | Map build system, config sources, external dependencies | sonnet |
| `samsara:yin-explorer` | Analyze silent failure paths, hidden coupling, unverified assumptions | sonnet |

## Implementation Flow

When executing a plan with multiple tasks, the implement skill orchestrates subagents:

```
Main agent                          Subagent (samsara:implementer)
    │                                        │
    ├─ Read index.yaml                       │
    ├─ Analyze task dependencies             │
    ├─ Dispatch (paste full text) ──────────>│
    │                                        ├─ STEP 0 (three questions)
    │                                        ├─ Write death tests
    │                                        ├─ Run death tests (red)
    │                                        ├─ Write unit tests
    │                                        ├─ Run unit tests (red)
    │                                        ├─ Implement (green)
    │                                        ├─ Write scar report
    │<────────────── Report back ────────────┤
    │                (no commit)             │
    ├─ Dispatch code-reviewer ──────────────>│ (samsara:code-reviewer)
    │<────────────── Review result ──────────┤
    ├─ Update index.yaml                     │
    ├─ Next task...                          │
    │   ...                                  │
    ├─ All tasks complete                    │
    ├─ Commit                                │
    └─ Transition to validate-and-ship       │
```

Key design decisions:
- **Subagents don't commit** — Only the main agent commits, after all tasks complete and reviews pass
- **Paste full text, not file paths** — The main agent curates context and injects it into the subagent prompt. Subagents never read task files themselves.
- **Samsara constraints are structural** — Baked into agent definitions, not injected via prompt. The implementer agent "is" a samsara implementer, not a generic agent told to follow samsara rules.

## Agent Constraints

These constraints are enforced on all agents operating under Samsara.

### Prohibited Behaviors

1. **No silent completion** — Incomplete input must be flagged, never auto-filled with assumptions
2. **No confirmation bias** — Don't only implement the happy path. Always mark: "when ___ is not true, ___ happens"
3. **No implicit assumptions** — Every assumption must be explicit: "This assumes ___. If not true, ___ happens"
4. **No optimistic completion** — Unknown side effects and edge cases must be listed in the completion report
5. **No swallowing contradictions** — When requirements contradict, stop and surface the contradiction

### Mandatory Behaviors

1. After every implementation: "This implementation will silently fail when: ___"
2. After every design proposal: "This design assumes ___ is always true. If not, ___ rots first"
3. Before every optimization: "Is this worth optimizing, or should it not exist?"
4. On ambiguous requirements: Don't pick the most reasonable interpretation — make the ambiguity visible

## Project Structure

```
samsara/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata (name, version)
├── agents/
│   ├── code-reviewer.md         # Yin-side code review
│   ├── implementer.md           # Death-test-first implementation
│   ├── infra-explorer.md        # Infrastructure analysis
│   ├── structure-explorer.md    # Codebase structure mapping
│   └── yin-explorer.md          # Silent failure analysis
├── hooks/
│   ├── hooks.json               # SessionStart hook registration
│   ├── session-start            # Injects samsara-bootstrap at session start
│   └── check-codebase-map       # Reminds to generate codebase map if missing
├── skills/
│   ├── samsara-bootstrap/       # Session initialization (axiom + constraints)
│   ├── research/                # Problem investigation + kickoff
│   ├── planning/                # Death-first spec + task generation
│   ├── implement/               # Subagent orchestration + scar reports
│   │   ├── SKILL.md
│   │   ├── dispatch-template.md # Prompt template for subagent dispatch
│   │   └── scar-report.md      # Scar report format reference
│   ├── validate-and-ship/       # Validation + ship manifest
│   ├── fast-track/              # Compressed workflow for small changes
│   ├── debugging/               # Four-phase yin-side debugging
│   ├── codebase-map/            # Project structural + failure surface mapping
│   └── writing-skills/          # TDD for skill development
└── MEMORY.md                    # Plugin memory index
```

## Artifacts

Samsara produces structured artifacts throughout the workflow:

| Phase | Artifact | Format | Purpose |
|-------|----------|--------|---------|
| Research | Kickoff | Markdown | Problem framing + scope |
| Research | Problem autopsy | Markdown | Death cases + silent failure analysis |
| Planning | Overview | Markdown | Architecture context for subagents |
| Planning | Tasks | Markdown | Individual task specs with death test requirements |
| Planning | Acceptance criteria | YAML | Success + failure conditions |
| Planning | Index | YAML | Task list with dependencies |
| Implement | Scar report | YAML | Per-task wounds: assumptions, silent failures, edge cases |
| Validate | Ship manifest | YAML | Delivery summary with failure budget |

## Version

Current version: **0.5.0**

## License

MIT
