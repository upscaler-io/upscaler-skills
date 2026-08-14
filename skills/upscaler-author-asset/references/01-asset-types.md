# 01 — Asset types, subtypes, and count ranges

The Upscaler platform recognises four **asset categories**. Each category has a fixed set of **subtypes**; each subtype has a recommended **count range** (the same ranges the platform's built-in AI generator uses when planning assets). Always read this file first — it is the source of truth for every other reference in this skill.

## Categories at a glance

| Category | Unit of structure | What it produces |
| --- | --- | --- |
| `document` | section (numbered `## N.`) | Narrative prose: policy, procedure, guideline, plan |
| `register` | section (`##` + `---` + fields) | Data collection templates with form fields |
| `record` | task (one Markdown body per task; titles in the definition payload) | Multi-page workflow forms with sequenced tasks |
| `course` | lesson (page boundary `# Lesson N:`) | Multi-lesson training with mandatory assessments |

## Subtypes and count ranges (authoritative)

These are recommended ranges, not publish-time constraints: the platform's publish validator only checks per-block options, so an out-of-range asset still publishes. Stay in range anyway — the ranges mirror what the platform's own AI generator enforces internally, and they keep assets consistent with the section templates.

### Document — unit: sections

| Subtype | Min | Max | Typical use |
| --- | --- | --- | --- |
| `policy` | 5 | 9 | Mandatory rules ("shall" language) |
| `procedure` | 6 | 10 | Step-by-step process (SOP) |
| `guideline` | 4 | 7 | Recommendations, best practices |
| `plan` | 5 | 9 | Strategy, roadmap, programme |

### Register — unit: sections (total fields: 10–20+)

| Subtype | Min sections | Max sections | Typical use |
| --- | --- | --- | --- |
| `risk_register` | 3 | 5 | Risk log with likelihood/impact scales |
| `asset_register` | 3 | 5 | Information asset inventory |
| `supplier_register` | 3 | 4 | Third-party vendor tracking |
| `improvement_register` | 3 | 5 | OFIs, corrective actions |
| `audit_register` | 3 | 4 | Audit findings log |

### Record — unit: tasks

| Subtype | Min tasks | Max tasks | Typical use |
| --- | --- | --- | --- |
| `audit_record` | 2 | 4 | Audit header + findings + conclusion |
| `meeting_minutes` | 2 | 3 | Meeting details + actions |
| `incident_record` | 3 | 5 | Raise & assess + BCP + lessons + close |

### Course — unit: lessons

| Subtype | Min lessons | Max lessons | Typical use |
| --- | --- | --- | --- |
| `compliance_training` | 3 | 6 | Mandatory training (GDPR, security awareness) |
| `product_training` | 3 | 10 | Platform / feature training |
| `onboarding_course` | 2 | 6 | Induction for new joiners |

## Trigger-keyword map (for detection)

Given a user prompt, map to `(category, subtype)` by matching the first hit.

| Keywords (case-insensitive substring) | Category | Subtype |
| --- | --- | --- |
| `policy`, `policies` | `document` | `policy` |
| `procedure`, `process`, `sop`, `standard operating` | `document` | `procedure` |
| `guideline`, `guidance`, `best practice(s)` | `document` | `guideline` |
| `plan`, `strategy`, `roadmap`, `programme`, `program` | `document` | `plan` |
| `risk register`, `risk log`, `risk management` | `register` | `risk_register` |
| `asset register`, `asset inventory`, `asset list` | `register` | `asset_register` |
| `supplier register`, `vendor register`, `supplier list`, `vendor list`, `third party register` | `register` | `supplier_register` |
| `improvement register`, `improvement log`, `ofi register`, `opportunity for improvement`, `continual improvement` | `register` | `improvement_register` |
| `audit register`, `audit findings register`, `audit finding log`, `audit tracker` | `register` | `audit_register` |
| `audit`, `audit record`, `audit report`, `audit finding` | `record` | `audit_record` |
| `meeting`, `minutes`, `mom`, `meeting notes` | `record` | `meeting_minutes` |
| `incident`, `incident record`, `incident report`, `security incident` | `record` | `incident_record` |
| `compliance training`, `security awareness training`, `security training`, `mandatory training`, `compliance course`, `gdpr training`, `data protection training` | `course` | `compliance_training` |
| `product training`, `platform training`, `user training`, `feature training`, `software training`, `editors training` | `course` | `product_training` |
| `onboarding`, `onboarding course`, `induction`, `new joiner`, `new starter`, `orientation` | `course` | `onboarding_course` |

**Generic fallbacks** when no specific subtype matches:
- `register` → `risk_register`
- `record` → `incident_record`
- `course` / `training` → `compliance_training`
- otherwise → `document` / `policy`

## Explicit type hint

If the user's specification contains an explicit `Type: <value>` line or a `| **Type** | <value> |` table row, honour that over keyword matching. Allowed values: `document`, `policy`, `procedure`, `guideline`, `plan`, `register`, `record`, `course`, `training`.

## Choosing within a category

When the prompt implies a category but not a subtype, ask the user before defaulting — the wrong subtype produces the wrong section template and count range.
