# 04 — Register authoring

Registers are single-page data collection templates: Markdown section headings interleaved with `<form-*>` elements. One continuous document; no task markers.

> **Notice:** Subtype field sets below are sensible defaults aligned with ISO 31000 / ISO 27001 practice. The live Upscaler platform is the authoritative source for the current default shape and may evolve these templates over time.

## Structure

```
# Register Title

## 1. Section Name

---

<form-* ...></form-*>

<form-* ...></form-*>

## 2. Next Section

---

<form-* ...></form-*>
```

Rules:
- One `# H1` — the register title.
- Each section starts with `## N. Title`, then a blank line, then `---`, then a blank line, then the first field.
- `---` appears **only** between heading and first field of each section. Never after fields. Never at the end of the register.
- 3–6 sections total; field count 10–20+ depending on subtype (see `01-asset-types.md`).
- Every field is a `<form-*>` element from `02-form-elements.md`.
- Every field `name` is a fresh ID from `scripts/generate_field_id.py`. IDs unique across the whole register.
- Every field has `guidance` (2–4 sentences). Every field except `form-radio`, `form-checkbox`, and `form-recordlink` also has `placeholder`: an example prefixed `E.g.`, or an empty string for date/member fields where no example applies. `form-radio`, `form-checkbox`, and `form-recordlink` have no placeholder option, so omit the attribute entirely (the worked example below already does this for radios).

## Field count guidelines

A well-shaped register has ~10–20 fields grouped as:

| Field group | Count | Typical fields |
| --- | --- | --- |
| Identification | 2–3 | Auto-increment ID, name/title, category |
| Description | 2–4 | Details, notes, context |
| Ownership | 1–2 | Owner, responsible party |
| Assessment / Rating | 3–5 | Likelihood, impact, status, priority |
| Tracking / Dates | 2–4 | Date added, review date, frequency |
| Additional context | 2–4 | Controls, compliance references, related items |

At least 3–5 fields should be `required="true"`.

## Field-type selection

| Data shape | Use |
| --- | --- |
| Short text (< 100 chars) | `form-text` |
| Long text (descriptions, notes) | `form-text-area` |
| Numeric values | `form-number` |
| Single choice, 2–4 options | `form-radio` |
| Single choice, 5+ options | `form-select` with `mode=""` |
| Single choice with visual rating | `form-radio` with the rating colour scale |
| Multiple choices (5+) | `form-select` with `mode="multiple"` |
| Multiple choices (2–4) | `form-checkbox` |
| Date | `form-date-picker` |
| Yes / No | `form-radio` with 2 options (Yes=`volcano`, No=`green`) |
| Sequential ID | `form-auto-increment` (prefix from register title) |
| Assign a team member | `form-member` |

## Subtype templates

### risk_register (default 3 sections, ~11 fields)

1. **Risk Details** — Risk Number (`form-auto-increment`, prefix `RSK-`), Description (`form-text-area`), Category (`form-select`), Owner (`form-member`)
2. **Risk Assessment** — Likelihood (`form-radio`, 5-point colour scale), Impact (`form-radio`, 5-point colour scale), Risk Score (`form-number`, calculated — optional), Current Controls (`form-text-area`), Applicable Frameworks (`form-select`, `mode="multiple"`)
3. **Risk Treatment** — Treatment Plan (`form-text-area`), Status (`form-radio`, solid style), Next Review Date (`form-date-picker`)

### asset_register (default 3 sections, ~11 fields)

1. **Asset Information** — Asset Name (`form-text`), Asset Type (`form-select`), Description (`form-text-area`), Owner (`form-member`)
2. **Classification** — Contains PII (`form-radio` Yes/No), Asset Value (`form-radio`, colour scale), Location / Hosted By (`form-text`)
3. **Compliance** — Applicable SLA (`form-text`), Applicable Regulations (`form-select` multi), Stakeholders (`form-member` multi), Date Added (`form-date-picker`)

### supplier_register (default 3 sections, ~9 fields)

1. **Supplier Information** — Name (`form-text`), Service Description (`form-text-area`), Category (`form-select`), Contract Owner (`form-member`)
2. **Contract Details** — Expiry Date (`form-date-picker`), Data Access Level (`form-radio`, colour scale), Review Frequency (`form-select`)
3. **Status** — Supplier Status (`form-radio`, solid), Last Assessment Date (`form-date-picker`)

### improvement_register (default 3 sections, ~10 fields)

1. **Improvement Details** — Improvement Number (`form-auto-increment`, prefix `IMP-`), Description (`form-text-area`), Source (`form-select`), Business Area (`form-text`), Owner (`form-member`)
2. **Review** — Date Reviewed (`form-date-picker`), Management Decision (`form-radio`), Associated Actions (`form-text-area`)
3. **Status** — Implementation Status (`form-radio`, solid), Effectiveness (`form-radio`, colour scale)

### audit_register (default 3 sections, ~9 fields)

1. **Finding Details** — Finding Number (`form-auto-increment`, prefix `AUD-`), Description (`form-text-area`), Audit Area (`form-text`), Severity (`form-radio`, colour scale)
2. **Corrective Action** — Action Required (`form-text-area`), Owner (`form-member`), Due Date (`form-date-picker`)
3. **Status** — Status (`form-radio`, solid), Completion Date (`form-date-picker`)

## Worked example — risk_register

```markdown
# Information Security Risk Register

## 1. Risk Details

---

<form-auto-increment name="ff_WrjkP1fN6A365o3cveo6woPvJEbk" title="Risk Number"
  required="true" placeholder="E.g. RSK-000001"
  guidance="Auto-assigned sequential ID for each new risk entry. Do not edit manually."
  nextNumber="1" addLeadingZeros="true" expectedMaxNumber="999999"
  prefix="RSK-"></form-auto-increment>

<form-text-area name="ff_S8hLCiPi7ybgWiiP5xGRfQiPCyWH" title="Risk Description"
  required="true"
  placeholder="E.g. Unauthorised access to customer data via compromised credentials."
  guidance="Describe the risk scenario and potential impact in enough detail for a reader unfamiliar with the risk to understand it. Avoid jargon."></form-text-area>

<form-select name="ff_3rwpHqJmtS5EdIZx0qqvpEx5VUZg" title="Risk Category"
  required="true" placeholder="E.g. Operational"
  guidance="Select the category that best describes this risk." mode=""
  values='[{"text":"Strategic","color":null},{"text":"Operational","color":null},{"text":"Financial","color":null},{"text":"Compliance","color":null},{"text":"Information Security","color":null}]'></form-select>

<form-member name="ff_Mj9ofnfAO2nn2uFjNSLOah1oAKE8" title="Risk Owner"
  required="true" placeholder=""
  guidance="Select the person accountable for managing this risk. Ownership should sit with a single named individual, not a team."
  multiple="false" includeGroups="false"></form-member>

## 2. Risk Assessment

---

<form-radio name="ff_3gMVRbwX96YETFnyYWiHxQ9U3BG1" title="Likelihood" required="true"
  guidance="Assess the probability of this risk occurring within the next 12 months, assuming current controls remain in place."
  optionType="button" supportCalculatedValue="true"
  values='[{"text":"1 - Rare","color":"green","calculatedValue":1},{"text":"2 - Unlikely","color":"cyan","calculatedValue":2},{"text":"3 - Possible","color":"gold","calculatedValue":3},{"text":"4 - Likely","color":"orange","calculatedValue":4},{"text":"5 - Almost Certain","color":"volcano","calculatedValue":5}]'></form-radio>

<form-radio name="ff_SDsJ6B5SXXr4oUgrCmCBOaRd5CxH" title="Impact" required="true"
  guidance="Assess the potential impact if the risk materialises. Consider financial, reputational, operational, and regulatory effects."
  optionType="button" supportCalculatedValue="true"
  values='[{"text":"1 - Insignificant","color":"green","calculatedValue":1},{"text":"2 - Minor","color":"cyan","calculatedValue":2},{"text":"3 - Moderate","color":"gold","calculatedValue":3},{"text":"4 - Major","color":"orange","calculatedValue":4},{"text":"5 - Severe","color":"volcano","calculatedValue":5}]'></form-radio>

<form-number name="ff_MArpjGPvLT5v9yUe2ols3AQcGLW1" title="Risk Score"
  required="false" placeholder=""
  guidance="Automatically calculated as Likelihood multiplied by Impact. Do not enter a value manually; the platform recomputes it on every change."
  calculated="true"
  formula="{{ff_3gMVRbwX96YETFnyYWiHxQ9U3BG1}} * {{ff_SDsJ6B5SXXr4oUgrCmCBOaRd5CxH}}"></form-number>

<form-text-area name="ff_7WcmjwIYncn2cow3CUJwnRx0DtF4" title="Current Controls"
  required="false"
  placeholder="E.g. MFA on all admin accounts; quarterly access review."
  guidance="List the controls already in place that mitigate this risk. Include technical, administrative, and physical controls where relevant."></form-text-area>

<form-select name="ff_uqvmoLSGQIbIFjZycM9tmKztfukY" title="Applicable Frameworks"
  required="false" placeholder="E.g. ISO 27001"
  guidance="Select all compliance frameworks relevant to this risk." mode="multiple"
  values='[{"text":"ISO 27001","color":null},{"text":"ISO 9001","color":null},{"text":"GDPR","color":null},{"text":"SOC 2","color":null}]'></form-select>

## 3. Risk Treatment

---

<form-text-area name="ff_ZE1Mc56kCRsmk2qpJ9qs5CtuUf3H" title="Treatment Plan"
  required="true"
  placeholder="E.g. Implement MFA across all privileged accounts by Q3."
  guidance="Describe the planned treatment strategy. Cover accept, avoid, transfer, or mitigate, and the specific actions to be taken."></form-text-area>

<form-radio name="ff_4W2pz3sDjkXlictARlJCAgIKaRAA" title="Treatment Status" required="true"
  guidance="Indicate the current status of the treatment plan."
  optionType="button"
  values='[{"text":"Not Started","color":null},{"text":"In Progress","color":null},{"text":"Implemented","color":null},{"text":"Closed","color":null}]'></form-radio>

<form-date-picker name="ff_kQxG6WfptorhsxpC3jg9KoOTGIUI" title="Next Review Date"
  required="true" placeholder=""
  guidance="Select the date the risk assessment should be revisited. Typically every 6–12 months, or sooner after a control change."
  defaultToday="false"></form-date-picker>
```

## Common mistakes

- `---` appearing after fields or at the end of the register.
- Hand-crafted field names (`risk-owner`, `ff_NMbi2t4oVJqw5u0TTWIjwzp890bc`) — must be a fresh `ff_` + 28-char ID.
- Reusing the same `name` across fields.
- `form-checkbox` with object values — use plain strings.
- Rating `form-radio` without `optionType="button"`. Do not write a `buttonStyle` attribute — it is ignored; the platform renders outline buttons automatically when values carry colours and solid buttons when they do not.
- Yes/No `form-radio` without the `volcano`/`green` colour pairing.
- Authoring or writing a value into a field with `calculated="true"` — the platform recomputes it on every form change and renders the input disabled; a manually written value is overwritten or ignored. Formula variables may only reference `form-number` fields, `form-table` columns, or fields with `supportCalculatedValue="true"`.
- Fewer than 10 fields total.
