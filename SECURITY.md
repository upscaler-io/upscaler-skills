# Security Policy

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Report it privately by one of these channels:

- GitHub: on the **Security** tab of this repository, click
  **Report a vulnerability**.
- Email: write to **support@upscaler.io**.

Include a description, reproduction steps, and the plugin version (from
`.codex-plugin/plugin.json`) or the commit SHA. We aim to acknowledge within
3 business days and to ship a fix or a mitigation plan within 30 days.

## Scope

This repository is the `upscaler-skills` plugin. In scope:

- the skills under `skills/`
- the build and validation scripts under `scripts/`
- the shared guidance under `references/`
- `.mcp.json`, which points agents at the Upscaler MCP server
- the plugin manifests in `.claude-plugin/` and `.codex-plugin/`

Vulnerabilities in the Upscaler API, the web application or `upscaler-cli` are
in scope for the same address but are tracked separately.
