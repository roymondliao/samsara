# Problem Autopsy: codebase-map-churn-autoregen

## original_statement

> "Codebase map 的重要性被放大，卻是需要提高該 codebase map 的主動性，而不是被動更新。另外也要對 codebase 對 project 的檢驗機制做一下 review，看是哪邊需要優化或是刪除。"

Follow-up clarifications (verbatim intent):
> "真正的痛點是『沒人會去跑 /samsara:codebase-map 重生』-> 這是一點，所以需要可以被自動化"
> "如果已 live codebase 為準，那 map 只是一張預覽地圖，協助更快找到內容而已"
> trigger points: "a / b 都是" (session start + pre-thinking entry)
> "Codebase map 要保留，這機制很重要"

## reframed_statement

The codebase-map is a preview/navigation aid, not a source of truth (live codebase wins on conflict). Its current freshness mechanism is dishonest (mtime-based, gamed by `touch`/checkout) and ineffective (warn-only, and nobody acts on the warning). The real problem is that manual regeneration never happens, so the map silently decays into a misleading preview. Solve it by replacing the wall-clock/mtime signal with a code-churn signal anchored to the map's `last_updated`, and by auto-regenerating the map at session start and at pre-thinking entry when churn exceeds a threshold — failing honestly (mark stale + record reason) when regeneration cannot complete.

## translation_delta

```yaml
translation_delta:
  - original: "提高該 codebase map 的主動性"
    reframed: "auto-regenerate the map when churn is over threshold (not: make a better warning)"
    delta: "The user's earlier-implied 'proactive = mark unreliable / block workflow' was rejected during interrogation. Since the map is only a preview (live wins), blocking on it is wrong; the correct proactivity is automatic regeneration, because warn-only has already demonstrably failed (65 days ignored)."
  - original: "看是哪邊需要優化或是刪除"
    reframed: "delete the wall-clock staleness_threshold_days proxy; keep (do not delete) the map and the hook"
    delta: "The 'delete' the user meant lands on the wrong proxy (7-day threshold + mtime), not on the map or hook. User explicitly confirmed the map and mechanism stay."
  - original: "codebase map 的重要性被放大"
    reframed: "the map is a low-stakes navigation aid because live codebase is authoritative"
    delta: "Interrogation downgraded the stakes: staleness does NOT cause silent correctness failures (live wins). The value at risk is navigation speed and trust, not correctness. This lowers the priority/severity framing but does not kill the work."
  - original: "提高主動性 (when to trigger)"
    reframed: "trigger detection+regen at BOTH session start (a) and pre-thinking entry (b)"
    delta: "User chose both trigger points, not background (c). Cost falls on the user at those points but is gated behind the churn threshold."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "If churn-based staleness cannot be computed reliably in common environments (no git history / shallow clone / detached HEAD) more often than it succeeds"
    rationale: "A churn signal that is itself frequently unknown is just a new dishonest proxy replacing the old one — better to keep an explicit, honest 'age unknown' state than ship an unreliable churn number"
  - condition: "If the codebase-map skill cannot be invoked non-interactively / automatically"
    rationale: "Auto-regeneration is the core of the reshaped problem; if regeneration fundamentally requires human interaction, the whole automation premise collapses and the work should stop at 'honest churn-based warning' rather than fake an auto path"
  - condition: "If auto-regen cost at session start proves intrusive enough that users disable the hook"
    rationale: "A disabled hook delivers zero benefit at full maintenance cost — at that point the mechanism should not exist in that form"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "The session/user at the auto-regen trigger point (session start or pre-thinking entry)"
    cost: "Pays the token + time cost of a full codebase-map regeneration when churn is over threshold, possibly while trying to do something unrelated"
  - who: "CI / unattended automation environments"
    cost: "If the hook triggers regeneration without a human present, it may slow CI or produce unexpected map changes/commits"
  - who: "Future maintainers of the freshness logic"
    cost: "Freshness moves from 'manual but simple' to 'automatic but more complex' (churn computation, threshold, throttle, both trigger points, failure handling) — a new mechanism that must itself be maintained and can itself rot"
```

## observable_done_state

In a repo whose churn is over threshold: **not solved** → the map keeps its old content and emits a session-start reminder that nobody acts on, while mtime can falsely report it fresh. **Solved** → staleness is computed from code churn since `last_updated` (mtime is never the signal), and at session start and pre-thinking entry the map is automatically regenerated to reflect current churn. When auto-regeneration cannot complete, the map is explicitly marked stale with the failure reason recorded — it is never silently reused as if fresh.
