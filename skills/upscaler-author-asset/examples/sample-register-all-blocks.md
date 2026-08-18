# Information Security Risk Register — All Blocks Showcase

## 1. Risk Identification

---

<form-auto-increment name="ff_QRZwrEOGlZ2V3hTmqIBgxCkPvS8y" title="Risk Number"
  required="true" placeholder="E.g. RSK-000001"
  guidance="Auto-assigned sequential ID for each new risk entry. Do not edit manually; the platform will allocate the next number on save."
  nextNumber="1" addLeadingZeros="true" expectedMaxNumber="999999"
  prefix="RSK-"></form-auto-increment>

<form-text name="ff_TaAF0p59NV8dEtAOFQJfy794bu0Z" title="Risk Title"
  required="true" placeholder="E.g. Unauthorised access to customer data"
  guidance="Provide a short, descriptive title (under 100 characters) that summarises the risk. Keep it scannable for reviewers."></form-text>

<form-text-area name="ff_IC2OR2nE5GkiCH6T2pj2GrINz9Tx" title="Risk Description"
  required="true"
  placeholder="E.g. Compromised admin credentials could allow an attacker to exfiltrate customer records from the production database."
  guidance="Describe the risk scenario and potential impact in enough detail for a reader unfamiliar with the risk to understand it. Avoid jargon and include the threat source, vulnerability, and consequence."></form-text-area>

<form-select name="ff_EvpkcsXpRxsHzPaBIqGPUi6nDRHb" title="Risk Category"
  required="true" placeholder="E.g. Operational"
  guidance="Select the single category that best describes this risk for reporting purposes." mode=""
  values='[{"text":"Strategic","color":null},{"text":"Operational","color":null},{"text":"Financial","color":null},{"text":"Compliance","color":null},{"text":"Information Security","color":null}]'></form-select>

## 2. Classification and Scope

---

<form-select name="ff_F9L6p0FGQWsRdgvYH7mNmDLYpwXZ" title="Applicable Frameworks"
  required="false" placeholder="E.g. ISO 27001"
  guidance="Select all compliance frameworks relevant to this risk. Multiple selections are allowed for cross-framework risks." mode="multiple"
  values='[{"text":"ISO 27001","color":null},{"text":"ISO 9001","color":null},{"text":"GDPR","color":null},{"text":"SOC 2","color":null},{"text":"HIPAA","color":null}]'></form-select>

<form-checkbox name="ff_sg8vQ1IlQKMC7ovhZcu2C60I2A2h" title="Data Categories"
  required="false"
  guidance="Select all categories of data involved in this risk. Used for impact analysis and regulatory reporting."
  direction="horizontal"
  values='["Personal Data","Financial Data","Health Data","Proprietary Data"]'></form-checkbox>

<form-radio name="ff_oYhFiVOabKnRV0OB4FXf2O1xTRsR" title="Contains Personal Data"
  required="true"
  guidance="Indicate whether the risk involves personal data under GDPR. A Yes answer triggers additional data protection review."
  optionType="button"
  values='[{"text":"Yes","color":"volcano"},{"text":"No","color":"green"}]'></form-radio>

<form-number name="ff_VkZiRpoEf09AaXFN6FM2KsBWaofI" title="Estimated Financial Impact (GBP)"
  required="false" placeholder="E.g. 50000"
  guidance="Enter the estimated direct financial impact in GBP if the risk materialises. Leave blank if not quantifiable."></form-number>

## 3. Assessment

---

<form-radio name="ff_gU3JXyTPzkYk3SJeLd7ucZWBJgOD" title="Likelihood" required="true"
  guidance="Assess the probability of this risk occurring within the next 12 months, assuming current controls remain in place."
  optionType="button"
  values='[{"text":"1 - Rare","color":"green"},{"text":"2 - Unlikely","color":"cyan"},{"text":"3 - Possible","color":"gold"},{"text":"4 - Likely","color":"orange"},{"text":"5 - Almost Certain","color":"volcano"}]'></form-radio>

<form-radio name="ff_3iWkyoJtKLxBmk7gZN67jj10h3Pz" title="Impact" required="true"
  guidance="Assess the potential impact if the risk materialises. Consider financial, reputational, operational, and regulatory effects together."
  optionType="button"
  values='[{"text":"1 - Insignificant","color":"green"},{"text":"2 - Minor","color":"cyan"},{"text":"3 - Moderate","color":"gold"},{"text":"4 - Major","color":"orange"},{"text":"5 - Severe","color":"volcano"}]'></form-radio>

<form-radio name="ff_mEyrwVaZF77jsttNrrLvxStCDY5O" title="Treatment Status" required="false"
  guidance="Indicate the current status of the treatment plan. Update this value as the risk treatment progresses through its lifecycle."
  optionType="button"
  values='[{"text":"Not Started","color":null},{"text":"In Progress","color":null},{"text":"Implemented","color":null},{"text":"Closed","color":null}]'></form-radio>

## 4. Ownership and Tracking

---

<form-member name="ff_zNA6j0S8u3J1g9PHBtekLvJaSfzm" title="Risk Owner"
  required="true" placeholder=""
  guidance="Select the person accountable for managing this risk. Ownership should sit with a single named individual, not a team or group."
  multiple="false" includeGroups="false"></form-member>

<form-date-picker name="ff_URjxhry7vkXPLknJsDd7HlZyFjpi" title="Date Identified"
  required="false" placeholder=""
  guidance="Select the date this risk was first identified or raised for assessment. Used for ageing and trend reports."
  defaultToday="true"></form-date-picker>

<form-time-picker name="ff_cNv3EFozN7ABpuCXJI6RRfAlQclP" title="Detection Time"
  required="false" placeholder=""
  guidance="Record the approximate time of day the risk was detected, if known. Useful for incident-linked risks where timing matters."
  use12Hours="false" defaultNow="false"></form-time-picker>

<form-upload name="ff_A7rrVupXLClzLZb4VzQYDLgssIYs" title="Supporting Evidence"
  required="false" placeholder=""
  guidance="Upload supporting evidence such as screenshots, scan reports, emails, or threat intel. The form displays the platform-wide file limits automatically."
  multiple="true"></form-upload>

<!-- File limits are platform-global, not per-field: max 50 MB per file, max 30 files,
     allow-list of common document/spreadsheet/image/archive/data extensions.
     Never author maxCount / maxSize / accept, and never restate limits in guidance. -->

## 5. Related References

---

<form-table name="ff_Ya6g39cqRUo6TTIn4TugUlYlatqG" title="Control Actions"
  required="false" placeholder=""
  guidance="Document each control action as a row. Include a short action ID, an owner description, and a severity rating to help prioritise treatment."
  columns='[{"key":"col-id","title":"Action ID","dataIndex":"col-id","type":"form-text","options":{"title":"Action ID","placeholder":"E.g. CTL-001","guidance":"","required":false}},{"key":"col-owner","title":"Owner","dataIndex":"col-owner","type":"form-text","options":{"title":"Owner","placeholder":"E.g. IT Security Manager","guidance":"","required":false}},{"key":"col-severity","title":"Severity","dataIndex":"col-severity","type":"form-radio","options":{"title":"Severity","guidance":"","required":false,"optionType":"button","values":[{"text":"Minor","color":"gold"},{"text":"Major","color":"volcano"},{"text":"Critical","color":"magenta"}]}}]'></form-table>

<!-- TODO: replace REGISTER_ID_HERE with the actual risk register definition id -->
<form-lookup name="ff_FMEsPjTPKNKUz7KinDPsYCYRvYKA" title="Related Risks"
  required="false" placeholder=""
  guidance="Select any related risks already logged in the risk register. Linking related risks helps reviewers understand aggregated exposure."
  multiple="true" filterParentId='[{"label":"Risk Register","key":"REGISTER_ID_HERE","value":"REGISTER_ID_HERE"}]'></form-lookup>

<!-- TODO: replace RECORD_DEF_ID with an actual audit record definition id -->
<form-recordlink name="ff_8PoorMtMTJYTdTlZtuGw8dtHpP9A" title="Related Audit Records"
  required="false"
  guidance="Link to any audit records that surfaced or relate to this risk. Keeps the audit trail bidirectional for assurance reviews."
  recordDefinitions='[{"label":"Internal Audit Record","key":"RECORD_DEF_ID","value":"RECORD_DEF_ID"}]'></form-recordlink>

<form-asset-picker name="ff_ZwbIIaRhpP6ueEJ9jrLHJQPrpAji" title="Affected Assets"
  required="false" placeholder=""
  guidance="Select the documents or registers impacted by this risk. Sources cover document definitions and register definitions in the workspace."
  multiple="true" sources='["document_definition","register_definition"]'></form-asset-picker>
