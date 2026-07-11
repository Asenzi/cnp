---
name: product-safety
description: High-safety product security workflow for the Friends mini program. Use when designing, reviewing, or implementing anti-abuse controls for user generated content, erotic or illegal avatars, nickname/profile review, new-user influx risk, WeChat content security, third-party IMS moderation, user risk levels, rate limits, reports, backfills, audit logs, or product safety rollout plans.
---

# Product Safety

## Default Stance

Use a conservative product-safety posture:

```text
unreviewed content is invisible
review failure is not approval
new users are low-trust
backend state decides display
all review decisions are logged
```

For Friends, prefer the smallest change that enforces `reviewed before visible`.

## Workflow

1. Find the shared backend response path for each public surface before editing frontend pages.
2. Route mutable profile/content changes through review states: `pending`, `approved`, `rejected`, `review_failed`.
3. Gate display in shared response builders or serializers.
4. Use WeChat official content security as the first provider and third-party IMS as the second provider for high-safety surfaces.
5. Require dual approval for avatars, nicknames, bios, and public feed content.
6. Keep default/fallback content visible while review is pending, rejected, failed, or timed out.
7. Add rate limits and risk-level rules before adding complex moderation infrastructure.
8. Log provider request IDs, results, labels, timestamps, and final enforcement action.
9. Add a small runnable check for any non-trivial review-state or display-gating logic.

## Implementation Rules

- Avatars: never show a new avatar until its status is `approved`; use the default avatar for all other statuses.
- Nicknames: show the last approved nickname or a default nickname while a new nickname is under review.
- Bios/signatures: hide or show the last approved value unless the new value is `approved`.
- Public content: only approved content enters feeds, search, recommendations, notifications, or share cards.
- Provider timeout/error: keep content `pending` or `review_failed`; do not display.
- New users: enforce a protection window, profile edit frequency caps, and stricter review.
- Repeat violations: reset content, restrict profile edits, escalate risk level, then ban on serious or repeated abuse.
- Reports: lower exposure immediately for multi-report or high-risk reports, then recheck via IMS.
- Historical unsafe content: run backfill review for unreviewed, recently changed, reported, high-exposure, and repeat-offender content.
- Safety switches: keep a backend config switch to force all unapproved avatars/nicknames/content to fallback during incidents.

## Product Reference

Read [references/high-safety-plan.md](references/high-safety-plan.md) when the task needs product policy details, field names, rollout phases, punishment rules, metrics, or user-facing copy.
