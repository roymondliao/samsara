# Problem Autopsy: <feature-name>

<!-- Address every section with supported content. If a section lacks supporting
     input, replace its content with this exact marker:
     Input incomplete; missing: <specific information or evidence>.
     Do not invent a value or use TBD/N/A. -->

## original_statement
<!-- Verbatim problem statement from the user/stakeholder. Do not paraphrase. -->

## reframed_statement
<!-- Your understanding of the problem in your own words. -->

## translation_delta

```yaml
translation_delta:
  - original: "<exact phrase>"
    reframed: "<your version>"
    delta: "<what changed and why it matters>"
```

## kill_conditions

<!-- Add entries only for independently supported conditions. Do not duplicate
     or invent entries to satisfy a count. If none can be supported, use the
     missing-input marker instead of this block. -->

```yaml
kill_conditions:
  - condition: "<when to abandon this>"
    rationale: "<why>"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "<who bears cost>"
    cost: "<what cost>"
```

## observable_done_state
<!-- Three sentences max. What is the observable difference between "solved" and "not solved"? -->

## accepted_gaps
<!-- Auto/HITL accepted gaps from the four Research questions. Use decision refs,
     consequences, owner, and recheck signal; write "none" when empty. -->
