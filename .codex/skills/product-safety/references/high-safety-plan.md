# Friends Product Safety High-Safety Plan

## Security Goals

```text
Unreviewed content is not shown.
Rejected content is not shown.
Review failures are not treated as approval.
New users start with low trust.
High-risk users are automatically limited.
All review and enforcement decisions are traceable.
```

## Review Scope

Prioritize:

```text
avatar
nickname
bio/signature
posts
comments
chat images
circle avatar/cover/name/rules
```

Also apply the same model to any new public user-generated surface.

## Minimum Build

Build in this order. Do not start with a moderation dashboard unless these gates already exist.

```text
1. backend display gate: unapproved profile/content returns fallback
2. profile update API writes candidate fields with pending state
3. async review job calls WeChat and IMS
4. finalizer promotes approved candidates or rejects them
5. rate limits for new users and repeat violators
6. review logs and punishment logs
7. backfill job for existing unsafe content
8. report endpoint that rechecks and lowers exposure
```

Backend is the source of truth. Frontend can show review hints, but cannot decide whether a submitted avatar, nickname, bio, or public content is safe to display.

## Provider Strategy

Use two layers for high-safety surfaces:

```text
WeChat official content security -> third-party IMS -> local risk rules -> final state
```

Decision table:

```text
WeChat pass + IMS pass = approved
WeChat reject = rejected
IMS reject = rejected
provider timeout = pending or review_failed, not visible
provider error = review_failed, not visible
suspicious/high-risk = IMS recheck or reject by policy
```

Do not use "one provider passes, so display" for avatars, nicknames, bios, or public-feed content when safety level is high.

Provider adapter contract:

```text
check_image(url, context) -> provider_result
check_text(text, context) -> provider_result
provider_result.status: pass / reject / suspicious / error / timeout
provider_result.labels: provider risk labels
provider_result.request_id: provider trace id
```

Final decision:

```text
all required providers pass -> approved
any provider rejects -> rejected
any provider suspicious -> pending or rejected by risk policy
any provider timeout/error -> review_failed or pending, not visible
```

## Avatar Flow

```text
User uploads avatar
-> backend stores candidate URL
-> avatar_status = pending
-> frontend/API continues returning default or last approved avatar
-> WeChat image check
-> IMS image check
-> both pass: avatar_status = approved, candidate becomes visible
-> any reject: avatar_status = rejected, keep default/last approved avatar
-> timeout/error: avatar_status = review_failed or pending, keep fallback avatar
```

Display rule:

```text
avatar_status == approved ? approved_avatar_url : default_avatar_url
```

API response rule:

```text
return avatar_url only when avatar_status == approved
return default_avatar_url otherwise
do not leak avatar_candidate_url to public APIs
owner-only APIs may return candidate status for UI prompts
```

Never show unreviewed avatars in:

```text
home feed
user profile
comments
chat list
nearby/discovery
leaderboard
search
share card
notifications
circle/member lists
```

## Nickname And Bio Flow

```text
User submits nickname/bio
-> save candidate as pending
-> continue showing old approved value or default
-> WeChat text check
-> IMS text check
-> both pass: promote candidate to approved value
-> any reject: keep old/default value
```

Block or reject:

```text
pornographic implication
contact details and variants
QR-code or off-platform diversion hints
ads and spam
official impersonation
abuse/harassment
fraud or transaction bait
political/violent illegal content
symbol flooding
```

Avoid exposing exact rule hits to the user.

API response rule:

```text
public nickname = approved nickname or default nickname
public bio = approved bio or empty string
candidate nickname/bio visible only to the owner
```

Default names should be neutral, for example `用户1234`, not the rejected nickname.

## Posts, Comments, Chat, And Circles

Public posts/comments:

```text
submit -> pending -> review -> approved enters feed/search/recommendation
reject -> not visible
timeout/error -> pending or review_failed, not visible
```

Private chat:

```text
text: check before delivery for high-risk/new users
image: check before delivery or send blurred placeholder until approved
serious violation: block message and escalate user risk
```

Circle/user-created group surfaces:

```text
circle name/avatar/cover/rules all use pending candidates
unapproved circle cover/avatar falls back to default
unapproved circle name keeps old approved name or default
```

## New-User Protection

Default protection window:

```text
first 24 hours after registration
```

Limits:

```text
avatar changes: max 1/day
nickname changes: max 1/day
bio changes: max 1/day
comments/posts/private messages: stricter frequency caps
bulk friend adds/searches: limited
public exposure: reduced until normal behavior accrues
```

High-risk triggers:

```text
many registrations from same IP/device/channel
registers then immediately changes avatar or posts
multiple review failures
reports from other users
abnormal nickname/avatar patterns
```

Protection can be lifted by time plus normal behavior:

```text
account age > 24 hours
no review rejection
no reports
normal interaction pattern
phone/real-name/member status if already part of product trust model
```

## Risk Levels

```text
L0 normal user
L1 new user
L2 suspicious user
L3 high-risk user
L4 banned user
```

Escalation:

```text
new registration -> L1
same IP/device mass registration -> L2
frequent avatar/nickname changes -> L2
1 review failure -> L2
2 review failures -> L3
serious porn/fraud/diversion -> L3 or L4
repeated serious abuse -> L4
```

Actions:

```text
L0: normal use, content still reviewed
L1: rate limits and strict profile review
L2: reduced exposure, strict review, profile edit limits
L3: hide profile/public content, disable posting/profile edits
L4: ban account and linked identifiers
```

Linked identifiers can include `openid`, `unionid`, phone, device, IP, channel, and behavior fingerprint when available.

## Rate Limits

Suggested defaults:

```text
avatar normal users: 3/day
avatar new users: 1/day
avatar suspicious users: blocked for 7 days
nickname normal users: 1/7 days
nickname new users: 1/day
comments new users: 1/minute
comments normal users: 5/minute
registrations: cap by IP, device, phone, and channel
```

Use existing rate-limit infrastructure before adding new services.

When Redis or a shared limiter already exists, use it. Otherwise start with database counters by day; migrate later only if contention becomes real.

## Punishments

Avatar:

```text
1st violation: reset to default avatar and warn
2nd violation: block avatar changes for 24 hours
3rd violation: block profile edits for 7 days
serious erotic/illegal avatar: ban
```

Nickname/bio:

```text
1st violation: keep old/default value
2nd violation: block changes for 24 hours
3rd violation: block changes for 7 days
serious diversion/fraud/porn: ban
```

Content:

```text
light: do not show content
medium: mute 24 hours
serious: ban
batch abuse: ban account plus linked identifiers
```

## Reports And Backfill

Reports:

```text
user reports content
-> reduce exposure immediately for high-risk or multi-report content
-> send to IMS recheck
-> enforce reset/hide/ban when confirmed
-> log malicious reporters separately
```

Backfill:

```text
unreviewed avatars
recent 7-day new-user avatars
reported users
repeat offenders
high-exposure users
historical review-failed content
```

Run hourly during incidents, daily when stable.

Backfill must not make risky content more visible. During backfill, unknown status should display fallback until approved.

## Minimal Data Model

Profile fields:

```text
avatar_url
avatar_candidate_url
avatar_status
avatar_checked_at
nickname
nickname_candidate
nickname_status
bio
bio_candidate
bio_status
risk_level
profile_edit_blocked_until
muted_until
banned_at
```

Review log:

```text
id
user_id
content_type
content_value
provider
provider_request_id
provider_result
risk_labels
final_result
reject_reason
created_at
checked_at
```

Punishment log:

```text
user_id
punishment_type
reason
source
start_time
end_time
operator
```

Content review queue fields:

```text
id
content_type
content_id
user_id
status
attempt_count
next_retry_at
created_at
updated_at
```

Keep candidate values separate from approved public values. This prevents a rejected candidate from leaking through old API paths.

## Backend Enforcement Checklist

```text
All public user serializers call one avatar display helper.
All public user serializers call one nickname display helper.
No endpoint returns candidate avatar/nickname/bio except owner-only profile edit APIs.
Feed/search/recommendation queries filter to approved content.
Upload/update APIs write pending candidate fields, not approved fields.
Review finalizer is idempotent.
Provider callbacks/results verify request ownership before updating state.
Timeout/error states are invisible.
Rate limits run before storing candidate uploads when possible.
Punishments are checked before profile update, post, comment, or message actions.
```

Idempotency rule:

```text
same review job can run more than once without double punishment or stale promotion
only the latest candidate for a field can be promoted
```

## Frontend Enforcement Checklist

```text
Use API-returned display avatar/nickname; do not compose public values from candidate fields.
After upload, show default/old avatar plus "审核中".
Do not preview a pending erotic-risk image in public surfaces.
Show generic rejection copy.
Respect blocked_until/muted_until states.
Do not reveal provider labels or exact hit rules.
```

Frontend is only presentation. If frontend checks disagree with backend, backend wins.

## Safety Switches

Add backend config switches, preferably dynamic if the project already has config storage:

```text
force_default_avatar_for_unapproved = true
force_default_nickname_for_unapproved = true
require_dual_review_for_profile = true
new_user_protection_hours = 24
block_public_content_when_review_down = true
```

Incident mode:

```text
force all non-approved avatars to default
pause new profile candidate promotion
tighten new-user edit limits
run backfill for recent users
alert on provider failures and rejection spikes
```

## User Copy

Keep messages short and non-diagnostic:

```text
头像审核中，通过后将自动展示
头像不符合平台规范，请重新上传
昵称包含不合规内容，请修改后重试
由于近期资料修改异常，暂时无法修改
```

## Rollout Order

Stop the bleeding:

```text
all unreviewed avatars show default avatar
avatars become reviewed-before-visible
WeChat image/text checks integrated
new-user avatar change rate limit
violating avatars automatically reset
```

Raise safety:

```text
third-party IMS integrated
dual review for avatars/nicknames/bios
review failures stay invisible
review logs stored
```

Govern abuse:

```text
new-user protection
risk levels
IP/device/channel limits
report rechecks
historical backfill
automatic punishments
```

Operate long term:

```text
risk dashboard
violation-rate monitoring
channel quality analysis
review-cost monitoring
blacklist enrichment
rule updates
```

## Acceptance Tests

Minimum checks before release:

```text
pending avatar returns default avatar in public profile/list/feed APIs
rejected avatar returns default avatar
review_failed avatar returns default avatar
approved avatar returns approved URL
pending nickname returns old/default nickname
candidate avatar URL is absent from public APIs
new user cannot update avatar more than daily limit
provider timeout does not approve content
duplicate review job does not double punish
older candidate cannot overwrite newer approved candidate
public feed excludes pending/rejected posts
```

Use the smallest runnable test that proves these; no broad test suite is required just to validate one display helper.

## Metrics And Alerts

Track:

```text
new registrations
avatar changes
avatar rejection rate
nickname rejection rate
provider failure rate
review latency
reports
bans
registrations by IP/device/channel
violations by channel
```

Alert on:

```text
registration spike
avatar rejection spike
provider failure spike
channel violation spike
report spike
same IP/device registration spike
```
