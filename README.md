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

### Multi-Platform Support

Samsara is authored as a Claude Code plugin, but `samsara-cli` can convert and install it for other agent platforms (e.g., Codex):

```bash
source .venv/bin/activate
uv run samsara-cli list-platforms              # Show supported targets
uv run samsara-cli convert --platform codex    # Convert into ./dist/codex/
uv run samsara-cli install codex --scope project
uv run samsara-cli validate --platform codex   # Verify converted output
```

The converter translates skills, agents, hooks, and references into the target platform's format; `update` refreshes an existing installation.

## Workflow

Samsara routes state-changing engineering work through a death-first workflow.

> **Derived overview.** The canonical executable routing contract lives in
> [`skills/samsara-bootstrap/SKILL.md`](skills/samsara-bootstrap/SKILL.md).
> If this overview disagrees with that contract, the Bootstrap contract wins.

```
User request
├─ explicit Samsara skill command -> named skill
├─ read-only / explanation / meta-audit -> handle directly
├─ production failure -> debugging
│  ├─ bounded authorized repair -> fast-track -> done
│  └─ structural / wide / unknown repair -> research
├─ proven low-risk state change -> fast-track -> done
└─ other state-changing feature work
   └─ research
      ├─ Step 0: select and persist this workflow run's execution mode
      └─ interrogate -> pre-thinking -> planning -> implement
         -> iteration entry triage
            ├─ skip fix rounds
            └─ run feature-level fix rounds
         -> validate-and-ship
```

`validate-and-ship` starts with the security and privacy Step 0 gate. Workflow
transitions use a human gate or an `auto-gatekeeper` decision in auto mode.

## Auto Mode

Research Step 0 selects the workflow-run execution mode: `human-in-the-loop` or `auto`. It persists that mode in the feature's `1-kickoff.md`; Bootstrap only injects global policy and routes feature work to Research. `human-in-the-loop` keeps the existing workflow gates. In `auto`, the same workflow still runs from `research -> pre-thinking -> planning -> implement -> iteration -> validate-and-ship`, but former human questions and confirmations are routed to `samsara:auto-gatekeeper`.

The gatekeeper is the Staff-level workflow decision authority: symmetric with the human for gate judgment, but not for external execution authority or consent. It uses the Codebase Map for broad structural awareness, feature artifacts for change authority, and targeted live evidence for current truth.

The gatekeeper is the sole writer of `changes/<feature>/auto-decisions.md`. Each append-only entry preserves the exact prompt, concise answer, decision-changing reasons, evidence refs, uncertainty, and next action in a validated compact YAML block. Calling workflows wait for that decision; they do not rewrite it.

The mode is feature-scoped and workflow-run-specific; `samsara_config.yaml` is not supported. A separate feature does not inherit the current feature's mode. After an auto run starts, it does not reintroduce user gates during that run; uncertainty is recorded in `auto-decisions.md`, and security/privacy unknowns become high-uncertainty reject decisions.

### Skills

| Skill | When to use | Key output |
|-------|-------------|------------|
| `samsara:research` | Starting new feature work or investigating a problem | Kickoff doc + problem autopsy |
| `samsara:pre-thinking` | After research, before planning — always invoked | Pre-thinking audit log of user–LLM assumption gaps |
| `samsara:planning` | After pre-thinking commitment (Proceed / Accept gap) | Death-first spec + tasks with acceptance criteria |
| `samsara:implement` | Plan with tasks is ready | Code with death tests + scar reports |
| `samsara:iteration` | After every completed implement — cheap entry triage, then feature-level fixes only when needed | Final scar dispositions + index checkpoint |
| `samsara:validate-and-ship` | Implement/iteration complete — Step 0 runs the security & privacy STOP gate first | Ship manifest with failure budget |
| `samsara:fast-track` | Evidence proves bounded damage, no unresolved design, and deterministic verification | Bounded implementation, review, validation, and commit record |
| `samsara:debugging` | Production failure in existing code | Diagnosis artifacts plus repair routing; no implementation |
| `samsara:codebase-map` | No map exists, or its source commit differs from committed Git HEAD | Committed-snapshot graph: responsibilities, capabilities, relationships, flows, and silent failure surfaces |
| `samsara:level-analysis` | Auto Gatekeeper needs comparable engineering perspectives before a difficult judgment | Advisory Senior/Staff/Principal analysis; no gate decision |
| `samsara:writing-skills` | Creating, revising, or reviewing Samsara skills | Skill authoring and proportional verification guidance |

### Agents

Samsara includes specialized subagents that carry yin-side constraints in their definitions — they don't rely on prompt injection to maintain the framework's spirit.

| Agent | Purpose | Model |
|-------|---------|-------|
| `samsara:implementer` | Death-test-first implementation with scar reports | sonnet |
| `samsara:code-reviewer` | Yin-side code review: deletion before correctness, naming honesty, silent rot paths | sonnet |
| `samsara:code-quality-reviewer` | Structural quality review against 9 yin principles (S/O/L/I/D + cohesion, coupling, DRY, pattern) with file:line evidence | sonnet |
| `samsara:auto-gatekeeper` | Answers workflow gate questions in auto mode; records append-only decisions | sonnet |
| `samsara:structure-explorer` | Map module boundaries, dependencies, public interfaces | sonnet |
| `samsara:infra-explorer` | Map build system, config sources, external dependencies | sonnet |
| `samsara:yin-explorer` | Analyze silent failure paths, hidden coupling, unverified assumptions | sonnet |

Review agents load domain-specific checklists from `references/` (code review, code quality, IaC review, test contracts) and return `UNKNOWN` for unsupported domains instead of guessing.

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
│   ├── plugin.json              # Plugin metadata (name, version)
│   └── marketplace.json         # Release version source of truth
├── agents/
│   ├── auto-gatekeeper.md       # Auto-mode gate decisions (append-only record)
│   ├── code-reviewer.md         # Yin-side code review
│   ├── code-quality-reviewer.md # Structural quality review (9 yin principles)
│   ├── implementer.md           # Death-test-first implementation
│   ├── infra-explorer.md        # Infrastructure analysis
│   ├── structure-explorer.md    # Codebase structure mapping
│   └── yin-explorer.md          # Silent failure analysis
├── hooks/
│   ├── hooks.json               # SessionStart hook registration
│   ├── session-start            # Injects samsara-bootstrap at session start
│   └── check-codebase-map       # Compares map source commit with Git HEAD
├── skills/
│   ├── samsara-bootstrap/       # Session initialization (axiom + constraints)
│   ├── research/                # Problem investigation + kickoff
│   ├── pre-thinking/            # User–LLM assumption gap audit
│   ├── planning/                # Death-first spec + task generation
│   ├── implement/               # Subagent orchestration + scar reports
│   ├── iteration/               # Feature-level scar resolution
│   ├── validate-and-ship/       # Step 0 security & privacy gate + validation + ship manifest
│   ├── fast-track/              # Evidence-bounded direct implementation path
│   ├── debugging/               # Yin-side diagnosis + repair routing
│   ├── codebase-map/            # Project structural + failure surface mapping
│   ├── level-analysis/          # Advisory Senior/Staff/Principal analysis
│   └── writing-skills/          # Skill authoring + proportional verification
├── references/                  # Domain checklists loaded by review agents
├── samsara_cli/                 # Release tooling + multi-platform converter/installer
├── tests/                       # Plugin test suite (pytest)
├── docs/                        # Design, philosophy, development notes
├── changes/                     # Per-feature workflow artifacts (kickoff → ship manifest)
├── issue.md                     # Framework defects found during real-world usage
├── roadmap.md                   # Planned capability enhancements
└── MEMORY.md                    # Plugin memory index
```

## Artifacts

Samsara produces structured artifacts throughout the workflow:

| Phase | Artifact | Format | Purpose |
|-------|----------|--------|---------|
| Research | Kickoff | Markdown | Problem framing + scope |
| Research | Problem autopsy | Markdown | Death cases + silent failure analysis |
| Pre-thinking | Pre-thinking audit log | Markdown | User–LLM assumption gaps + commitment decision |
| Planning | Overview | Markdown | Architecture context for subagents |
| Planning | Tasks | Markdown | Individual task specs with death test requirements |
| Planning | Acceptance criteria | YAML | Success + failure conditions |
| Planning | Index | YAML | Task list with dependencies |
| Implement | Scar report | YAML | Per-task wounds: assumptions, silent failures, edge cases |
| Iteration | Updated scar state + index checkpoint | YAML | Feature-level dispositions, evidence, and resume state |
| Auto mode | Auto decisions | Markdown | Append-only gate decisions with rationale and uncertainty |
| Fast-track | Fast-track record | YAML | Evidence-bounded implementation, review, and validation record |
| Validate | Ship manifest | YAML | Delivery summary with failure budget |

All artifacts live under `changes/<feature>/` — per-feature directories are the authoritative workflow record.

## Release

`.claude-plugin/marketplace.json` `metadata.version` is the release source of truth.

When preparing a release:

```bash
source .venv/bin/activate
uv run samsara-cli release sync-version
uv run samsara-cli release check-version
```

`sync-version` updates `.claude-plugin/plugin.json` and `pyproject.toml` to match marketplace metadata. `check-version` fails if any version drifts before CI or the release workflow creates a tag.

The GitHub release workflow runs when a pull request is closed by merging into `main`. Branch protection is expected to require the PR CI workflow to pass before merge.

## Issues and Roadmap

Samsara applies its own philosophy to itself — wounds are recorded, not hidden:

- **[issue.md](./issue.md)** — Framework defects discovered during real-world usage, with error chains and root-cause analysis (e.g., ISSUE-001: planning File Map contradicting Key Decisions).
- **[roadmap.md](./roadmap.md)** — Planned capability enhancements identified through analysis. Currently tracks the loop engineering gap analysis (RM-001 ~ RM-005): scheduling heartbeat, auto-mode loop driver, worktree parallelism, global loop state, and outward connectors.

## License

MIT
