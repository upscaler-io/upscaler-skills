# Upscaler skill-library personas

Shared reference describing the three user personas the Upscaler agent skills target. Used by each skill to calibrate tone, default output format, and which workflows to surface.

The "skills they invoke" lists below cover the **core** library only (`upscaler-skills`). Advanced workflows — evidence packs, design-doc gap reviews, framework setup, management-review packs, status reports — ship separately in `upscaler-adv-skills`; the persona model is the same there.

## Compliance manager / ISMS owner (primary)

Day-to-day operator of the organization's ISMS. Owns policies, controls, evidence, the risk register, training, audit prep. Reads and writes inside Upscaler constantly.

- **Asks:** "What's the status of control A.5.1?", "Show me overdue evidence", "Which risks have no owner?", "Am I ready for surveillance?", "Find our incident response procedure."
- **Wants:** concise, citation-backed answers; the ability to pivot from a question into a workflow (build an evidence pack, draft a policy) without re-orienting the agent.
- **Output preference:** prose + bulleted citations, by default. Structured reports only on explicit ask ("build me a pack", "produce the gap report").
- **Skills they invoke:** `upscaler-ask` (entry point), `upscaler-write-entry` and `upscaler-run-record` (day-to-day register and record upkeep), occasionally `upscaler-author-asset`.

## Engineer / PM doing compliance-adjacent work

Builds product features. Touches compliance when shipping something that interacts with personal data, access control, third parties, or change-management. Lives in the IDE / PR review; uses Upscaler intermittently.

- **Asks:** "Does this PRD have ISO 27001 gaps?", "Which policy applies to this API?", "Do we need a DPIA for this change?"
- **Wants:** fast yes / no / where-to-look answers; advisory gap reviews of design docs; pointers into the ISMS rather than full reproductions.
- **Output preference:** brief, decision-oriented. Findings with severity + remediation, not narrative.
- **Skills they invoke:** `upscaler-ask` (for lookups). Their main workflow, advisory gap review of a design doc, is `upscaler-review-design` in `upscaler-adv-skills` — this library answers their lookup questions but does not perform the review.

## Author / policy writer

Creates and edits assets in Upscaler: policies, procedures, registers, records, training courses. Cares deeply about the platform's strict authoring grammar (field IDs, form-element whitelist, count ranges, content formats).

- **Asks:** "Draft a privileged-access procedure", "Author an incident-record definition with these fields", "Build a compliance training course on data classification."
- **Wants:** output that passes Upscaler validation on the first try. No invented form elements, no malformed attributes, no count-range violations.
- **Output preference:** the asset definition itself, in the platform's expected format, with no surrounding chatter.
- **Skills they invoke:** `upscaler-author-asset` (almost exclusively).

## Cross-persona notes

- All three personas land first on `upscaler-ask` when the request is exploratory. The Q&A skill routes to the specialist skills when intent is clear.
- Compliance manager is the primary persona for the library's surface area — when a tradeoff arises between brevity for the manager vs. depth for the auditor, favor the manager.
- Auditor / external-reviewer is **not** a target persona for this library; auditor-ready artifacts are produced by the advanced skills for the compliance manager to hand off.
