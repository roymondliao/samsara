# Overview: <feature-name>

## Goal
<!-- One sentence. -->

## Core Identity (L1 — cited from pre-thinking, not re-derived)
<!-- One or two lines: what this system, within feature scope, essentially IS.
     Structural decisions must serve this identity. Copied from pre-thinking.md
     Step 6 L1 handoff — planning does not rewrite it. -->

## Architecture
<!-- 2-3 sentences about approach. -->

## Tech Stack
<!-- Key technologies/libraries. -->

## Key Decisions
<!-- Decisions made during research/planning that affect implementation. -->
- <decision>: <rationale>

### Real Seams (L1 — single source of seam declarations)
<!-- Every seam that any task's `seam` field in index.yaml references MUST be
     declared here, and only here. Content comes from pre-thinking.md Step 4
     (Real seams) — planning MAPS tasks onto these seams and ANNOTATES them
     with planned-change evidence; it never invents a new seam. If task
     decomposition reveals a seam pre-thinking did not identify, STOP and
     return to pre-thinking (design-decision gap), do not declare it here. -->
- seam: <semantic-name>  <!-- e.g. parser-boundary — self-documenting, not a code -->
  what: <the module/abstraction boundary, one line>
  evidence: <already-happened (cite git/file ref) | domain-essential (rationale)>
  planned: <task ids that will extend it (planning's annotation), or "none">

## Death Cases Summary
<!-- Top 3 most dangerous silent failure paths from acceptance.yaml. -->
1. <death case>
2. <death case>
3. <death case>

## File Map
<!-- Which files will be created or modified. -->
- `path/to/file` — <responsibility>
