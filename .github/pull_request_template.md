<!--
Thanks for the PR! Keep it scoped to one layer/feature so history stays
retraceable. PRs target `dev` (not `main`) unless it's a release.
-->

## Summary
<!-- What does this PR do, in 1–3 sentences? -->

Closes #<!-- issue number -->

## Layer / phase
<!-- e.g. Auth, API poller, Frontend. Should match the linked issue. -->

## Changes
<!-- Bullet the key changes so a reviewer can scan them. -->
-
-

## How I tested it
<!-- Commands run, endpoints hit, screenshots. "It builds" is not testing. -->
-

## Checklist
- [ ] Branch is `feature/<name>` off `dev`
- [ ] Linked the issue with `Closes #...`
- [ ] CI is green (backend lint/boot, frontend install)
- [ ] No secrets committed; `.env.example` updated if new env vars were added
- [ ] FastAPI routes have Pydantic request/response models (if backend)
- [ ] React components are functional + hooks only (if frontend)
