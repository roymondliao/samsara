"""Death tests pinning the ENGINE / DATA module split (iteration-fix-1).

`_contract_tokens.py` once carried TWO death-reasons in one module:
  (a) the token-matching + step-parsing ENGINE (rx, token_present, concept_present,
      missing_concepts, concepts_covered_by, pinned_heading_offenders, numbered_steps,
      step_index_of_concept, the Token alias, ROOT) — changes here are about HOW a
      concept is matched / how a step list is parsed; and
  (b) the concept-group DATA (CONTRACT_GATE..DAMP_OVER_DRY, the STEP_* tuples, the
      REFERENCE_CONCEPTS aggregate, REFERENCE_PATH_RX) — changes here are about WHAT
      each instruction surface must carry.

Code-quality review flagged this 4 times as accumulating structural debt: a change to
the matching engine and a change to the concept catalog should not have to touch the
same file. The fix split the engine into `_token_lib.py` and kept the data in
`_contract_tokens.py`.

These death tests make the split SELF-GUARDING. They target the SILENT failure mode:
a future edit drops an engine helper back into `_contract_tokens.py` (or sprouts a
concept-group dict in `_token_lib.py`) — the two death-reasons silently RE-MERGE while
every behavioural test stays GREEN, because re-merging changes nothing about matching
behaviour. The first human to notice would be a 5th structural review pass, long after
the debt re-accumulated. These tests turn that silent re-merge LOUD.

  DC-SPLIT-DATA-HAS-ENGINE  `_contract_tokens.py` defines an engine/helper function
      (any module-level `def`) → the matching engine has leaked back into the data
      module; the death-reasons are re-merged. RED.
  DC-SPLIT-ENGINE-HAS-DATA  `_token_lib.py` assigns concept-catalog DATA at module
      level — a concept-group dict, the {**spread} REFERENCE_CONCEPTS aggregate, or a
      STEP_* token tuple → the concept catalog has leaked into the engine module;
      death-reasons re-merged. RED. (Bare token-string constants like REFERENCE_PATH_RX
      are data-by-convention, guarded by review not AST — see _concept_data_assignments.)

mutate-to-red: before the split (helpers still in `_contract_tokens.py`) the first
test is RED. After the split it is GREEN. The failure mode each test names IS that
test's contract, so the exact structural assertion is allowed here (death test, not a
brittle unit test).
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
DATA_MODULE = PKG_DIR / "_contract_tokens.py"
ENGINE_MODULE = PKG_DIR / "_token_lib.py"


def _module_functiondefs(path: Path) -> list[str]:
    """Names of every MODULE-LEVEL `def` (engine/helper functions) in `path`.

    Module-level only: a `def` nested inside a class/function is not an engine helper
    the split is about. We read top-level `ast.FunctionDef` nodes. `rx` etc. are the
    engine; their presence in the DATA module is the re-merge we forbid.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _concept_data_assignments(path: Path) -> list[str]:
    """Names of module-level assignments that carry concept-catalog DATA.

    Concept-catalog data is the DATA death-reason: it must live in
    `_contract_tokens.py`, never in the engine module. We flag, at module level:
      - any dict assignment (a `{...}` value) — covers BOTH the
        {concept_key: (tokens, ...)} concept groups AND the REFERENCE_CONCEPTS
        aggregate built with `{**GROUP, ...}` spreads (an AnnAssign whose dict
        uses spreads, which an earlier dict-of-tuples-only check missed); and
      - any tuple-of-tokens assignment (a `(...)` whose elements are string
        literals or calls) — the STEP_* token tuples.
    The engine module legitimately contains zero module-level dicts or token
    tuples (its constants are a re.compile() Call, a Path() Call, and a typing
    alias), so flagging these shapes yields no false positives today while
    catching a concept group, the aggregate, or a STEP_* tuple leaking in. Match
    on structural shape, not a name list, so a NEW data item is caught too.

    Known boundary (honest, not silently overstated): a BARE token-string
    constant such as `REFERENCE_PATH_RX = "test-contract\\.md"` is data-by-
    convention kept in the data module, but is NOT flagged here — a lone string
    is structurally indistinguishable from a legitimate engine config string, and
    flagging every string would make this guard itself brittle (the exact failure
    mode this feature forbids). Bare-string token constants are guarded by
    convention + review, not by this AST check.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if value is None:  # bare AnnAssign (`X: T`) with no assigned value
            continue
        is_concept_data = isinstance(value, ast.Dict) or (
            isinstance(value, ast.Tuple)
            and bool(value.elts)
            and all(isinstance(e, (ast.Constant, ast.Call)) for e in value.elts)
        )
        if not is_concept_data:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                offenders.append(target.id)
    return offenders


class TestModuleSplitIsSelfGuarding:
    def test_data_module_defines_no_engine_functions(self):
        # DEATH [DC-SPLIT-DATA-HAS-ENGINE]: _contract_tokens.py is DATA-only. If it
        # defines any module-level function, the matching/step-parsing engine has
        # leaked back in and the two death-reasons (matching engine vs concept catalog)
        # are re-merged in one file — the exact structural debt this iteration split
        # apart. This stays GREEN today and would silently re-rot without this guard.
        offenders = _module_functiondefs(DATA_MODULE)
        assert offenders == [], (
            "SILENT FAILURE [DC-SPLIT-DATA-HAS-ENGINE]: _contract_tokens.py defines "
            f"module-level function(s) {offenders}. The data module must carry NO "
            "matching/step-parsing engine code — those helpers belong in _token_lib.py. "
            "A helper here re-merges the two death-reasons (engine + concept catalog) "
            "into one file, re-accumulating the structural debt the split removed."
        )

    def test_engine_module_defines_no_concept_catalog_data(self):
        # DEATH [DC-SPLIT-ENGINE-HAS-DATA]: _token_lib.py is ENGINE-only. If it assigns
        # any concept-catalog DATA — a concept-group dict, the {**spread} aggregate, or
        # a STEP_* token tuple — the concept catalog has leaked into the engine module,
        # re-merging the two death-reasons from the other direction.
        offenders = _concept_data_assignments(ENGINE_MODULE)
        assert offenders == [], (
            "SILENT FAILURE [DC-SPLIT-ENGINE-HAS-DATA]: _token_lib.py assigns "
            f"concept-catalog data {offenders}. The engine module must carry NO "
            "concept-catalog DATA — concept groups, the REFERENCE_CONCEPTS aggregate, "
            "and STEP_* token tuples belong in _contract_tokens.py. Data here "
            "re-merges the two death-reasons into one file."
        )

    def test_both_split_modules_exist(self):
        # DEATH: if the engine module is deleted/renamed, the two tests above parse a
        # missing file and ERROR rather than guard the split. Pin both files exist so a
        # silent collapse of the split (re-merging everything back into one module by
        # deleting _token_lib.py) is caught here, not masked by an import error.
        assert DATA_MODULE.is_file(), (
            f"SILENT FAILURE: data module {DATA_MODULE} is missing — the split "
            "collapsed and the separation guards cannot run."
        )
        assert ENGINE_MODULE.is_file(), (
            f"SILENT FAILURE: engine module {ENGINE_MODULE} is missing — the engine "
            "was merged back into the data module, re-accumulating the structural debt."
        )
