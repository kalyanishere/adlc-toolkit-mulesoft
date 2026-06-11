# Presets

Stack-shaped starter configs for `.adlc/config.yml`. Each preset captures a common combination of MuleSoft surface areas, deploy targets, and CI patterns. Pick the one closest to your scope, copy it into your repo, and replace the placeholder values.

## Available presets

| File | Scope |
|------|-------|
| [mule-core.yml](mule-core.yml) | Mule 4.6+ app + DataWeave + MUnit + CloudHub 2.0 deploy. The right baseline for most MuleSoft projects without API Manager governance. |
| [mule-anypoint.yml](mule-anypoint.yml) | mule-core plus API Manager governance (client-id-enforcement, rate-limiting, JWT/OAuth2), Exchange asset publishing, and RTF-or-CloudHub deploy. The right baseline for a process / experience API or any public-facing endpoint. |

## How to use a preset

From inside the repo where you're running `/init`:

```bash
cp ~/.claude/skills-mulesoft/presets/mule-core.yml .adlc/config.yml
$EDITOR .adlc/config.yml
```

Replace every `<placeholder>` with a real value (project name, app prefix, Anypoint org id, environment, region). Don't leave placeholders in — skills will fail loudly when they try to use them, but it's faster to just fill them in up front.

## What's a preset, exactly

A preset is **scope shape, not org configuration**. It declares:

- Which Mule surface areas are in play (`api_layer`, `governance.api_manager_enabled`, `features.exchange_publishing`)
- Which sections are populated (e.g., `governance.required_policies` when API Manager is on)
- Sensible defaults (e.g., `mule_runtime: "4.6.0"`, `java_version: "17"`, `deploy_target: "cloudhub2"`)
- Example shape for the `repos:` and `orgs:` blocks

It does **not** contain:

- Real Anypoint org IDs, client IDs/secrets, environment IDs
- Specific app prefixes or asset names — leave those as placeholder strings
- Anything proprietary to a specific company's Anypoint setup

## Adding a new preset

If you have a MuleSoft scope combination not covered here (e.g., Marketing Cloud connector, Composer, on-prem-only, MCP-server-as-asset), drop a new YAML file in this directory and update the table above. Naming convention: `mule-<scope>.yml` or `mule-<scope>-<sibling-tech>.yml`.

Open a PR against the canonical toolkit — presets benefit from being shared.
