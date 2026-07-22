---
name: glean-mcp-eval
description: Use when helping a field team run a Glean MCP vs direct vendor MCP A/B evaluation in Claude Code. Guides setup, preflight, prompt runs, grading, reporting, and packaging using this repository's CLI.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Write
---

# Glean MCP Eval Skill

You help a Glean field team run the Glean MCP A/B Eval Kit.

## Assumptions

- The current project is the eval kit repo or contains `scripts/glean_mcp_eval.py`.
- The customer is using Claude Code as the host.
- The eval compares:
  - `glean` arm: Glean MCP only.
  - `direct` arm: direct vendor MCPs only.
- MCP isolation can be strict (`mcp/*.json` files control servers) or ambient (`claude mcp list` controls servers). Strict mode is preferred.

## Workflow

1. Confirm the working directory contains `scripts/glean_mcp_eval.py`.
2. If `eval.config.json` or `golden_prompts.tsv` are missing, ask the user which MCP mode they want. Default to strict mode for clean benchmarks.

   Strict mode:

   ```bash
   cp config/eval.config.strict.example.json eval.config.json
   cp prompts/golden_prompts.example.tsv golden_prompts.tsv
   mkdir -p mcp
   cp config/mcp.glean.example.json  mcp/glean.mcp.json
   cp config/mcp.direct.example.json mcp/direct.mcp.json
   ```

   Ambient mode:

   ```bash
   cp config/eval.config.ambient.example.json eval.config.json
   cp prompts/golden_prompts.example.tsv golden_prompts.tsv
   ```

3. Help the user edit:
   - `eval.config.json`
   - `golden_prompts.tsv`
   - `mcp/glean.mcp.json` and `mcp/direct.mcp.json` when using strict mode

4. Run doctor:

   ```bash
   python3 scripts/glean_mcp_eval.py doctor --config eval.config.json
   ```

5. For each arm, run preflight before prompt execution:

   ```bash
   python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm glean --live
   python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm direct --live
   ```

6. Run arms with a stable anonymous participant id:

   ```bash
   python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm glean --participant-id test01
   python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm direct --participant-id test01
   ```

7. Grade only after both arms have paired results:

   ```bash
   python3 scripts/glean_mcp_eval.py grade --config eval.config.json --participant-id test01
   ```

8. Report and package:

   ```bash
   python3 scripts/glean_mcp_eval.py report --config eval.config.json
   python3 scripts/glean_mcp_eval.py package --config eval.config.json
   ```

## Guardrails

- Do not run an arm if latest live preflight fails or is missing unless the user explicitly overrides with `--force`.
- Keep prompt wording identical across arms.
- In strict mode, tell users not to manually switch MCP setup between arms; the JSON files isolate servers. In ambient mode, tell users to switch MCP setup and verify with `claude mcp list` before each arm.
- Remind users to use a tiny 1-2 prompt smoke test before a customer-facing run.
- Treat result zips as customer confidential.
