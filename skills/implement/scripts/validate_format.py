#!/usr/bin/env python3
"""Implement format validator — mechanical shape checks for scar reports.

Scope: FORMAT only (machine-decidable). This script never judges whether a
structural decision is a good bet, whether a refusal is wise, or whether a
forced_by ref is genuinely RELEVANT — those are judgment and belong to the
reviewers. It checks the mechanical shape the reviewers and aggregators
depend on, so a silent skip becomes a visible missing.

Checks per changes/<feature>/scar-reports/task-N-scar.yaml:
  scar-parse           file parses as YAML with a task_id
  dual-face            every structural_decisions entry carries both faces:
                       decision + forced_by (yang) AND refused + risk_if_wrong
                       (yin); serves_seam key present (null allowed)
  forced-by-resolves   every forced_by ref resolves to something checkable:
                       `task-N` ids exist in index.yaml (and when the citing
                       task's affects/depends context is available, the cited
                       task is reachable from it); `seam: <name>` resolves to
                       overview.md Real Seams; `git:`/file refs point at paths
                       that exist
  seam-resolves        serves_seam (non-null) resolves to a declared seam
  systemic-ref         every systemic_ref id exists in .samsara/systemic-scars.yaml
                       (a dangling id is a parse failure at aggregation time)
  debt-consistency     debt_registered is true when shortcuts / silent failure
                       conditions exist
  length-budget        known_shortcuts/silent_failure_conditions/
                       assumptions_made slot fields, items, structural_decisions
                       entries, narrative, and the whole report stay within the
                       budgets scar-schema.yaml's Budget section declares (char
                       caps read the YAML-decoded value, so a folded/literal
                       scalar cannot hide length behind fewer source lines)
  legacy-form          new known_shortcuts/silent_failure_conditions items
                       must use the what/bites_when/where slot form — a
                       `description` blob or a bare plain-string item is a
                       budget-evasion escape hatch (schema legacy-invalid).
                       systemic_ref items are exempt (their form did not
                       change). Does not apply to assumptions_made, which
                       never used `description`.
  slot-required        every non-systemic_ref, non-legacy-form item in
                       known_shortcuts/silent_failure_conditions carries
                       what/bites_when/where

structural_decisions key policy: required for NEW reports —
`structural_decisions: []` = checked, no structural bet; a MISSING key is
reported as a finding (schema granularity-floor). Old reports predating the anchor are
this script's caller's concern; at implement handoff every report is new.
The same "every report is new" policy applies to length-budget/legacy-form/
slot-required: this validator runs once per feature-dir at implement handoff
(no cross-feature historical scan) and does not grandfather reports written
before this check existed — a pre-existing report in the same feature-dir
still using the legacy `description` form is a genuine, intended finding,
not a false positive.

Exit code: 0 = clean, 1 = findings, 2 = cannot validate.

Usage:
    python validate_format.py <feature-dir> [--repo-root <path>]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is not installed (pip install pyyaml).")
    print("This is an unknown outcome, not a pass.")
    sys.exit(2)

_TASK_ID_RE = re.compile(r"\btask-\d+\b")
_SEAM_REF_RE = re.compile(r"\bseam:\s*(\S+)")
_FILE_REF_RE = re.compile(r"\bgit:\s*([^\s:#]+)")
_SEAM_DECL_RE = re.compile(r"^\s*-\s*seam:\s*(\S+)", re.MULTILINE)

# Budget constants — MUST stay numerically identical to the Budget section of
# skills/implement/templates/scar-schema.yaml (task-2's landed values). A
# drift test (tests/test_skills/test_format_validators.py::
# test_implement_budget_constants_match_schema_declaration) parses that
# schema text and asserts equality against these; changing either side alone
# is a red test, by design (schema is the declared source, this module is
# the enforced gate — they must not silently diverge).
BUDGET_FIELD_CHARS = 200  # what/bites_when/accepted_because/resolution/note/assumption
BUDGET_WHERE_CHARS = 120  # `where` only
BUDGET_ITEM_LINES = 6  # single known_shortcuts/silent_failure_conditions item
BUDGET_STRUCTURAL_ENTRY_LINES = 10  # single structural_decisions entry
BUDGET_NARRATIVE_LINES = 10  # narrative content lines
BUDGET_REPORT_LINES = 90  # whole report file, physical lines incl. comments/blanks

# Char-capped field NAMES — kept as named constants (not inline tuples in the
# check functions) so CHAR_CAPPED_FIELD_NAMES below is derived from what is
# actually enforced, not a hand-maintained duplicate list. A sibling drift
# test asserts every name here appears in scar-schema.yaml's Budget block
# text, symmetric to the numeric drift test above: the validator enforcing a
# field the schema never declared, or the schema declaring a field the
# validator never caps, both go red.
_SLOT_CHAR_FIELDS = ("what", "bites_when", "accepted_because", "resolution")  # <=200
_WHERE_FIELD = "where"  # <=120
_ASSUMPTION_CHAR_FIELDS = ("assumption", "note")  # <=200
CHAR_CAPPED_FIELD_NAMES = (
    frozenset(_SLOT_CHAR_FIELDS) | {_WHERE_FIELD} | frozenset(_ASSUMPTION_CHAR_FIELDS)
)


def _declared_seams(feature_dir: Path) -> set[str]:
    overview = feature_dir / "overview.md"
    if not overview.is_file():
        return set()
    text = overview.read_text(encoding="utf-8")
    start = text.find("### Real Seams")
    if start == -1:
        return set()
    rest = text[start:]
    end = re.search(r"^#{1,3} ", rest[len("### Real Seams") :], re.MULTILINE)
    body = rest if end is None else rest[: end.start() + len("### Real Seams")]
    return set(_SEAM_DECL_RE.findall(body))


def _known_task_ids(feature_dir: Path) -> set[str]:
    index = feature_dir / "index.yaml"
    if not index.is_file():
        return set()
    try:
        data = yaml.safe_load(index.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return set()
    return {
        str(t.get("id")) for t in data["tasks"] if isinstance(t, dict) and t.get("id")
    }


def _registry_ids(repo_root: Path) -> set[str] | None:
    """Return systemic scar registry ids, or None when the registry is absent.

    Reads the registry's ONE documented/live schema: a top-level `entries:`
    list of `{id, description, first_recorded, applies_when}` dicts (see
    .samsara/systemic-scars.yaml's own header comment, and the doc-contract
    test pinning this shape in test_scar_schema_noise_rules.py). There is no
    `scars:` top-level-key form anywhere in this repo (checked by grep) —
    that shape was never real; do not resurrect it as a "just in case"
    fallback (Structural Honesty: a format with zero consumers earns no
    tolerance path).
    """
    registry = repo_root / ".samsara" / "systemic-scars.yaml"
    if not registry.is_file():
        return None
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict):
        return set()
    entries = data.get("entries")
    if not isinstance(entries, list):
        return set()
    return {str(e.get("id")) for e in entries if isinstance(e, dict) and e.get("id")}


def _iter_items(section: list | None) -> list[dict]:
    """Normalize a scar list section: plain strings become dicts (schema legacy-invalid)."""
    items: list[dict] = []
    for item in section or []:
        if isinstance(item, str):
            items.append({"description": item})
        elif isinstance(item, dict):
            items.append(item)
    return items


def _normalize_item(raw: object) -> dict | None:
    """Normalize ONE raw scar-list entry (schema legacy-invalid), or None if the
    entry is neither a string nor a dict.

    Deliberately separate from `_iter_items`: that helper DROPS malformed
    entries, which shifts every later index out of alignment with the raw
    YAML list position (and therefore with yaml.compose()'s node indices).
    Callers that cross-reference a node (line-count checks) or just want an
    honest reported index enumerate the RAW list and normalize per-entry
    instead, so a stray malformed entry cannot misalign anything after it.
    """
    if isinstance(raw, str):
        return {"description": raw}
    if isinstance(raw, dict):
        return raw
    return None


def _iter_raw_items(data: dict, section_name: str) -> Iterator[tuple[int, dict | None]]:
    """Yield (raw-list-index, normalized-item-or-None) for a scar list
    section. Shared by the 3 checks that scan known_shortcuts/
    silent_failure_conditions/assumptions_made, so the raw-index-alignment
    contract (_normalize_item's docstring) lives in exactly one place."""
    for i, raw in enumerate(data.get(section_name) or []):
        yield i, _normalize_item(raw)


def _narrative_line_count(root: object) -> int | None:
    """Physical content lines of the `narrative` field, or None if absent.

    Uses yaml.compose() node marks (same technique as _node_line_count)
    rather than a text-position regex: a block scalar's start_mark sits on
    the KEY's own line (verified empirically), so content lines = the
    node's line span minus 1; an inline scalar has a zero line span (value
    and key share a line), so content is exactly 1 line. On a duplicate
    `narrative:` top-level key (itself a separate schema violation) this
    keeps the LAST occurrence, matching yaml.safe_load()'s dict semantics
    instead of silently reading a different one than what was loaded.
    """
    if not isinstance(root, yaml.MappingNode):
        return None
    value_node = None
    for key_node, candidate in root.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == "narrative":
            value_node = candidate
    if value_node is None:
        return None
    span = value_node.end_mark.line - value_node.start_mark.line
    return 1 if span <= 0 else span - 1


def _get_sequence_node(root: object, key: str) -> yaml.SequenceNode | None:
    """Return the SequenceNode value of a top-level mapping key, or None."""
    if not isinstance(root, yaml.MappingNode):
        return None
    for key_node, value_node in root.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == key:
            return value_node if isinstance(value_node, yaml.SequenceNode) else None
    return None


def _node_line_count(seq_node: yaml.SequenceNode | None, index: int) -> int | None:
    """Physical source lines spanned by seq_node.value[index], or None if
    the index is out of range. Callers MUST pass the RAW list index (from
    enumerating the section list directly, not a filtered/normalized copy)
    so this always lines up with the true YAML sequence position."""
    if seq_node is None or index >= len(seq_node.value):
        return None
    node = seq_node.value[index]
    return node.end_mark.line - node.start_mark.line


def _char_cap_finding(
    where: str, field_name: str, value: object, cap: int
) -> str | None:
    """One length-budget char-cap check, used at all 4 char-capped-field call
    sites (slot fields / where / systemic_ref note / assumptions_made) so the
    comparison and message format cannot drift apart between them."""
    if isinstance(value, str) and len(value) > cap:
        return (
            f"length-budget: {where} {field_name} is {len(value)} chars, over "
            f"the {cap}-char field budget"
        )
    return None


def _check_length_budget(
    name: str, data: dict, text: str, root_node: object
) -> list[str]:
    """FORMAT-only length checks (chars/lines), all under the `length-budget`
    finding class. Char caps read the yaml.safe_load()-decoded value, which
    is style-independent (plain/folded/literal all decode to the same
    string) — this is what defeats a folded scalar hiding length behind
    fewer source lines (DC-E)."""
    findings: list[str] = []

    total_lines = len(text.splitlines())
    if total_lines > BUDGET_REPORT_LINES:
        findings.append(
            f"length-budget: {name} report is {total_lines} lines, over the "
            f"{BUDGET_REPORT_LINES}-line report budget"
        )

    narrative_lines = _narrative_line_count(root_node)
    if narrative_lines is not None and narrative_lines > BUDGET_NARRATIVE_LINES:
        findings.append(
            f"length-budget: {name} narrative is {narrative_lines} lines, over "
            f"the {BUDGET_NARRATIVE_LINES}-line narrative budget"
        )

    for section_name in ("known_shortcuts", "silent_failure_conditions"):
        seq_node = _get_sequence_node(root_node, section_name)
        for i, item in _iter_raw_items(data, section_name):
            where = f"{name} {section_name}[{i}]"
            lines = _node_line_count(seq_node, i)
            if lines is not None and lines > BUDGET_ITEM_LINES:
                findings.append(
                    f"length-budget: {where} is {lines} lines, over the "
                    f"{BUDGET_ITEM_LINES}-line item budget"
                )
            if item is None or "description" in item:
                continue  # legacy-form/malformed items carry no slot fields to cap
            if item.get("systemic_ref"):
                finding = _char_cap_finding(
                    where, "note", item.get("note"), BUDGET_FIELD_CHARS
                )
                if finding:
                    findings.append(finding)
                continue
            for key in _SLOT_CHAR_FIELDS:
                finding = _char_cap_finding(
                    where, key, item.get(key), BUDGET_FIELD_CHARS
                )
                if finding:
                    findings.append(finding)
            finding = _char_cap_finding(
                where, "where", item.get(_WHERE_FIELD), BUDGET_WHERE_CHARS
            )
            if finding:
                findings.append(finding)

    for i, item in _iter_raw_items(data, "assumptions_made"):
        if item is None:
            continue
        where = f"{name} assumptions_made[{i}]"
        for key in _ASSUMPTION_CHAR_FIELDS:
            finding = _char_cap_finding(where, key, item.get(key), BUDGET_FIELD_CHARS)
            if finding:
                findings.append(finding)

    decisions = data.get("structural_decisions")
    if isinstance(decisions, list) and decisions:
        seq_node = _get_sequence_node(root_node, "structural_decisions")
        for i in range(len(decisions)):
            lines = _node_line_count(seq_node, i)
            if lines is not None and lines > BUDGET_STRUCTURAL_ENTRY_LINES:
                findings.append(
                    f"length-budget: {name} structural_decisions[{i}] is "
                    f"{lines} lines, over the {BUDGET_STRUCTURAL_ENTRY_LINES}"
                    "-line structural-entry budget"
                )

    return findings


def _check_legacy_form(name: str, data: dict) -> list[str]:
    """`description` blob / bare plain-string items are the schema's
    legacy-invalid form for NEW reports (DC-A budget-evasion escape hatch).
    systemic_ref items never carry `description` and are exempt by shape;
    assumptions_made never used `description` and is not scanned here."""
    findings: list[str] = []
    for section_name in ("known_shortcuts", "silent_failure_conditions"):
        for i, item in _iter_raw_items(data, section_name):
            if item is not None and "description" in item:
                findings.append(
                    f"legacy-form: {name} {section_name}[{i}] uses the legacy "
                    "`description` blob/plain-string form — new items must "
                    "use the what/bites_when/where slot form"
                )
    return findings


def _check_required_slots(name: str, data: dict) -> list[str]:
    """what/bites_when/where are required on every slot-form item. Legacy-
    form items (already flagged above) and systemic_ref items (their own,
    unchanged form) are exempt from this check."""
    findings: list[str] = []
    for section_name in ("known_shortcuts", "silent_failure_conditions"):
        for i, item in _iter_raw_items(data, section_name):
            if item is None or "description" in item or item.get("systemic_ref"):
                continue
            where = f"{name} {section_name}[{i}]"
            missing = [
                key
                for key in ("what", "bites_when", "where")
                if not str(item.get(key) or "").strip()
            ]
            if missing:
                findings.append(
                    f"slot-required: {where} missing required slot(s): "
                    f"{', '.join(missing)}"
                )
    return findings


def validate_scar(
    scar_path: Path,
    known_ids: set[str],
    seams: set[str],
    registry: set[str] | None,
    repo_root: Path,
) -> list[str]:
    name = scar_path.name
    text = scar_path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"scar-parse: {name} does not parse as YAML: {exc}"]
    if not isinstance(data, dict) or not data.get("task_id"):
        return [f"scar-parse: {name} has no task_id"]

    findings: list[str] = []

    # --- legacy-form / slot-required / length-budget (task-3) ---
    findings.extend(_check_legacy_form(name, data))
    findings.extend(_check_required_slots(name, data))
    try:
        root_node = yaml.compose(text)
    except yaml.YAMLError:
        root_node = None  # already surfaced by the safe_load parse above if fatal
    findings.extend(_check_length_budget(name, data, text, root_node))

    # --- systemic_ref dangling check across all scar list sections ---
    for section_name in (
        "known_shortcuts",
        "silent_failure_conditions",
        "assumptions_made",
    ):
        for item in _iter_items(data.get(section_name)):
            ref = item.get("systemic_ref")
            if not ref:
                continue
            if registry is None:
                findings.append(
                    f"systemic-ref: {name} {section_name} cites `{ref}` but "
                    ".samsara/systemic-scars.yaml does not exist"
                )
            elif str(ref) not in registry:
                findings.append(
                    f"systemic-ref: {name} {section_name} cites `{ref}` which is "
                    "not in .samsara/systemic-scars.yaml (dangling id = parse "
                    "failure at aggregation time)"
                )

    # --- debt consistency (mechanical: lists non-empty => flag true) ---
    has_debt = bool(_iter_items(data.get("known_shortcuts"))) or bool(
        _iter_items(data.get("silent_failure_conditions"))
    )
    if has_debt and data.get("debt_registered") is not True:
        findings.append(
            f"debt-consistency: {name} has shortcuts/silent-failure items but "
            "debt_registered is not true"
        )

    # --- structural_decisions ---
    if "structural_decisions" not in data:
        findings.append(
            f"dual-face: {name} has no structural_decisions key — write "
            "`structural_decisions: []` when the task made no structural bet "
            "(missing key = never considered, schema granularity-floor)"
        )
        return findings

    decisions = data.get("structural_decisions") or []
    if not isinstance(decisions, list):
        findings.append(f"dual-face: {name} structural_decisions is not a list")
        return findings

    for i, entry in enumerate(decisions):
        where = f"{name} structural_decisions[{i}]"
        if not isinstance(entry, dict):
            findings.append(f"dual-face: {where} is not a map")
            continue
        if not str(entry.get("decision") or "").strip():
            findings.append(f"dual-face: {where} has no `decision`")
        forced_by = entry.get("forced_by") or []
        if not forced_by:
            findings.append(
                f"dual-face: {where} has empty `forced_by` — a structural bet "
                "with no citable force should not have been written (schema forced-by-evidence)"
            )
        if not str(entry.get("refused") or "").strip():
            findings.append(f"dual-face: {where} missing yin face `refused`")
        if not str(entry.get("risk_if_wrong") or "").strip():
            findings.append(f"dual-face: {where} missing yin face `risk_if_wrong`")
        if "serves_seam" not in entry:
            findings.append(
                f"dual-face: {where} missing `serves_seam` key (null allowed)"
            )

        seam = entry.get("serves_seam")
        if seam not in (None, "null", "") and str(seam) not in seams:
            findings.append(
                f"seam-resolves: {where} serves_seam `{seam}` is not declared "
                "in overview.md Real Seams"
            )

        for ref in forced_by:
            ref_str = str(ref)
            resolved = False
            for tid in _TASK_ID_RE.findall(ref_str):
                resolved = True
                if tid not in known_ids:
                    findings.append(
                        f"forced-by-resolves: {where} cites `{tid}` which is not "
                        "a task in index.yaml"
                    )
            for seam_ref in _SEAM_REF_RE.findall(ref_str):
                resolved = True
                if seam_ref not in seams:
                    findings.append(
                        f"forced-by-resolves: {where} cites seam `{seam_ref}` "
                        "not declared in overview.md Real Seams"
                    )
            for file_ref in _FILE_REF_RE.findall(ref_str):
                resolved = True
                if not (repo_root / file_ref).exists():
                    findings.append(
                        f"forced-by-resolves: {where} cites `git: {file_ref}` "
                        "which does not exist in the repo"
                    )
            if not resolved:
                findings.append(
                    f"forced-by-resolves: {where} forced_by entry resolves to "
                    f"nothing checkable (no task id / seam / git ref): {ref_str!r}"
                )

    return findings


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    repo_root = Path.cwd()
    if "--repo-root" in args:
        idx = args.index("--repo-root")
        repo_root = Path(args[idx + 1])
        del args[idx : idx + 2]
    if len(args) != 1:
        print(__doc__)
        return 2

    feature_dir = Path(args[0])
    scar_dir = feature_dir / "scar-reports"
    if not scar_dir.is_dir():
        print(f"CANNOT VALIDATE: {scar_dir} does not exist")
        return 2
    scar_files = sorted(scar_dir.glob("*.yaml")) + sorted(scar_dir.glob("*.yml"))
    if not scar_files:
        print(f"CANNOT VALIDATE: no scar reports in {scar_dir}")
        return 2

    known_ids = _known_task_ids(feature_dir)
    seams = _declared_seams(feature_dir)
    registry = _registry_ids(repo_root)

    findings: list[str] = []
    for scar in scar_files:
        findings.extend(validate_scar(scar, known_ids, seams, registry, repo_root))

    if findings:
        for line in findings:
            print(f"FINDING {line}")
        print(f"\n{len(findings)} finding(s). Fix and re-run until clean.")
        return 1

    print(
        f"implement format validation: clean — {len(scar_files)} scar report(s) "
        "(parse / dual-face / forced-by / seam / systemic-ref / debt / "
        "length-budget / legacy-form / slot-required)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
