# Acceptance Scenario Taxonomy

Reference definitions only. Executable Planning procedure lives in `flow.md`;
artifact shape lives in `templates/acceptance.yaml`.

- **death_path:** the system appears correct while the required outcome is wrong
  or absent.
- **degradation:** a fallback changes service quality or guarantees.
- **unknown_outcome:** the system cannot determine whether the operation happened.
- **happy_path:** success with observable evidence, not a success assertion alone.

Record only applicable, evidence-backed scenarios. When degradation or unknown
outcome cannot occur, use `not_applicable` with a concrete rationale instead of
inventing a scenario.
