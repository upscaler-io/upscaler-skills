# 06 — Course authoring

Courses are **multi-page training content**. Each page is a **lesson** separated by `# Lesson N: Title`. Every lesson must end with a `<form-assessment>` quiz (≥3 MCQs).

> **Notice:** Lesson structure and assessment defaults below follow common instructional-design practice. The live Upscaler platform is the authoritative source for the current default shape and may evolve these templates over time.

## Structure

```
# Lesson 1: Lesson Title

## Training video

---

[Video placeholder: topic description]

## Learning objectives

---

* Objective 1
* Objective 2
* Objective 3

## Content section heading

---

Paragraph text explaining the topic.

> **Note**: optional callout for warnings or tips.

## Assessment

---

<form-assessment ...></form-assessment>

# Lesson 2: Next Lesson
...
```

Rules:
- Each lesson boundary is `# Lesson N: Title` matching the agreed plan.
- **No asset-level H1**: the course title lives in platform metadata, not in the content.
- All section headings inside a lesson use `##` — never `###` or deeper.
- Each section: `## Heading`, blank line, `---`, blank line, content. `---` only between heading and content.
- **Every lesson has exactly one `<form-assessment>`** with ≥3 questions, 3 answers each, exactly one `isCorrect: true` per question. No exceptions.
- Assessment `name` uses a fresh `scripts/generate_field_id.py` ID. Question and answer `id`s are simple `q1/q2/q3` and `a1/a2/a3` — do **not** call `generate_field_id` for those.
- Assessment field IDs are unique across the entire course.
- Stay within the lesson count range from `01-asset-types.md`: compliance 3–6, product 3–10, onboarding 2–6.
- No trailing blank lines at the end of the output.

## Section order within a lesson

1. **Training video** — always first. Use `[Video placeholder: topic]`.
2. **Learning objectives** — bullet list of 3–5, starting with action verbs.
3. **Content sections** — one or more `##` sections of prose + callouts.
4. **Hands-on exercise** — optional, as a `> **Note**:` callout with a practical task.
5. **Assessment** — **mandatory, always last**. Exactly one `<form-assessment>`.

## Allowed content blocks

| Block | Syntax |
| --- | --- |
| Section heading | `## Heading` |
| Paragraph | Plain text (2–4 sentences each) |
| Bullet list | `* Item` |
| Horizontal rule | `---` (always after heading) |
| Note callout | `> **Note**: text` (limit 1–2 per lesson) |
| Video placeholder | `[Video placeholder: topic]` |
| Mermaid diagram | ` ```mermaid ... ``` ` fenced block (≤10 nodes) |
| Assessment | `<form-assessment ...></form-assessment>` (mandatory, one per lesson) |

Do **not** emit: `form-text`, `form-select`, `form-table`, or any other `<form-*>` element in courses. The only form element allowed is `<form-assessment>`.

## Learning objectives

- 3–5 objectives per lesson.
- Start with an action verb: Understand, Identify, Recognise, Apply, Demonstrate, Learn, Know.
- Specific and measurable.

## Language conventions

| Context | Tense | Example |
| --- | --- | --- |
| Learning objectives | Infinitive (action verb) | "Understand the principles of data protection" |
| Instructional content | Present, second person | "In this lesson, you will learn to identify phishing" |
| Descriptions | Present, factual | "This lesson covers three phishing indicators" |
| Procedures | Imperative | "Open the settings panel" |
| Examples | Past or present tense | "A phishing email was received by Finance" |

### Subtype flavour

- `compliance_training` — formal, reference regulatory obligations explicitly.
- `product_training` — practical, include hands-on exercises.
- `onboarding_course` — welcoming, mix organisational context with platform training.

## Duration estimation (for planner previews)

| Lesson type | Duration |
| --- | --- |
| Introduction / summary | 3–5 min |
| Content-heavy lesson | 5–10 min |
| Add for assessment | +2–3 min |

## Assessment format (critical)

See `02-form-elements.md` for the full `<form-assessment>` rules. Summary:

- Attributes use **single** quotes, not double (`name='ff_...'`).
- `questions` holds a JSON array; strings inside use double quotes.
- **No apostrophes** anywhere inside `label` strings — they break the single-quoted attribute. Rephrase: "the organisation" not "the organisation's".
- Minimum 3 questions; each with 3 answers and exactly one `isCorrect: true`.
- `required='true'` always.
- `title='Lesson N: Assessment'`.
- `cover` (optional) — markdown intro shown with the Start button before the quiz begins, e.g. `cover='Answer all questions to complete this lesson.'`. The same single-quote and no-apostrophe rules apply to its text.

Single-correct is Upscaler house style for generated courses, mirroring the platform's own course-generator style guide; the runtime itself accepts multiple `isCorrect: true` answers with exact-set matching, so a stray extra `isCorrect: true` will not error — it silently requires learners to select every marked answer to pass.

## Worked example — compliance_training (Lesson 1 only)

```markdown
# Lesson 1: Introduction to Data Protection

## Training video

---

[Video placeholder: 2-minute welcome covering why data protection matters]

## Learning objectives

---

* Understand why data protection regulations exist
* Identify what counts as personal data
* Recognise the lawful bases for processing personal data
* Know where to go for help if you have a data protection question

## Why data protection matters

---

Data protection law exists to protect people from harm that can result from the misuse of information about them. When organisations process personal data carelessly, individuals can suffer financial loss, reputational damage, or loss of control over their identities.

In the UK and EU, the General Data Protection Regulation (GDPR) sets the core rules for how personal data must be handled. It gives individuals rights over their data and places strict obligations on organisations that collect and use it.

> **Note**: Breaches of the GDPR can result in fines up to 4% of global annual turnover. More importantly, they erode trust with customers and staff.

## What counts as personal data

---

Personal data is any information that can identify a living person, directly or indirectly. This includes obvious identifiers like names, email addresses, and phone numbers, but it also includes less obvious ones.

Examples of personal data:

* Full name, email address, and phone number
* IP addresses and device identifiers
* CCTV footage of a recognisable individual
* Employee ID combined with job title and department

Some types of personal data are **special category** and require extra protection — data revealing racial or ethnic origin, political opinions, religious beliefs, trade union membership, health data, or biometric identifiers.

## Lawful basis for processing

---

Before any organisation processes personal data, it must identify a lawful basis. The six lawful bases under the GDPR are:

* Consent
* Contract
* Legal obligation
* Vital interests
* Public task
* Legitimate interests

Each basis has its own conditions and implications. The organisation documents its lawful basis for every processing activity.

## Assessment

---

<form-assessment name='ff_x5jct9to5xOuqB1IgUqMZ8KjdfS8' title='Lesson 1: Assessment'
  required='true' questions='[
  {"id":"q1","label":"Which of the following is an example of personal data?","answers":[
    {"id":"a1","label":"A persons full name combined with their email address","isCorrect":true},
    {"id":"a2","label":"Aggregated sales figures for the last quarter","isCorrect":false},
    {"id":"a3","label":"The publicly registered address of a limited company","isCorrect":false}
  ]},
  {"id":"q2","label":"How many lawful bases for processing personal data does the GDPR define?","answers":[
    {"id":"a1","label":"Three","isCorrect":false},
    {"id":"a2","label":"Six","isCorrect":true},
    {"id":"a3","label":"Ten","isCorrect":false}
  ]},
  {"id":"q3","label":"Which category of data requires additional protection under the GDPR?","answers":[
    {"id":"a1","label":"Job title","isCorrect":false},
    {"id":"a2","label":"Special category data such as health information","isCorrect":true},
    {"id":"a3","label":"Company email address","isCorrect":false}
  ]}]'></form-assessment>
```

## Publish flow (course shell + lessons)

The `# Lesson N:` bundle is an authoring artifact only. The platform does not split those headings into lesson nodes. Before publishing, split it into one body file per lesson and remove each lesson's H1 boundary; the title is passed separately.

Create the empty course shell, capture its `cd_*` ID, then add and populate each lesson in order:

```bash
upscaler asset create --type course_definition \
  --data '{"title":"Security Awareness","description":"Annual awareness training"}' --dry-run
upscaler asset create --type course_definition \
  --data '{"title":"Security Awareness","description":"Annual awareness training"}'

# Capture cd_* from create and cl_* from add-lesson.
upscaler asset add-lesson --asset-id <cd_*> --title "Introduction" --dry-run
upscaler asset add-lesson --asset-id <cd_*> --title "Introduction"
upscaler asset set-lesson-values --asset-id <cd_*> --lesson-id <cl_*> \
  --values-file lesson-1.md --values-type markdown --dry-run
upscaler asset set-lesson-values --asset-id <cd_*> --lesson-id <cl_*> \
  --values-file lesson-1.md --values-type markdown
```

Repeat `add-lesson` + `set-lesson-values` for every lesson. Use `set-lesson-title`, `set-lesson-description`, `remove-lesson`, and `move-lesson` for later edits.

MCP maps to the same structured sequence:

```text
upscaler_manage_asset({operation:"create", asset_type:"course_definition", data:{title, description}})
upscaler_manage_asset({operation:"add_lesson_definition", asset_id:"<cd_*>", data:{title, description}})
upscaler_manage_asset({operation:"set_lesson_definition_values", asset_id:"<cd_*>", data:{lessonDefinitionId:"<cl_*>", values:"<lesson markdown>", valuesType:"markdown"}})
```

There is no batch `lessons[]` create payload today. Do not put `tasks[]` on a course; that payload is record-definition-only.

## Common mistakes

- Missing `<form-assessment>` on any lesson.
- Assessment with fewer than 3 questions, fewer than 3 answers, or multiple `isCorrect: true` (style violation; the platform will not reject it, but learners must then select all marked answers to pass).
- **Apostrophes inside `label` strings** — the most common failure. `"The organisation's policy"` breaks the attribute; rewrite as `"The organisation policy"` or `"The policy of the organisation"`.
- Using double quotes on assessment attributes instead of single quotes.
- Calling `generate_field_id()` for every question / answer `id` — only the assessment `name` gets one.
- Reusing assessment `name`s across lessons.
- Including form fields other than `form-assessment` in a lesson.
- Placing the assessment anywhere other than last.
- Missing the video placeholder `[Video placeholder: …]` in the first section.
- Sending the whole `# Lesson N:` bundle as course `values`; it creates no lesson definitions. Split it and use the lesson operations above.
