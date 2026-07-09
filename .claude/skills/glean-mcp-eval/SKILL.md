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
  - `glean` arm: Glean MCP enabled, direct vendor MCPs disabled.
  - `direct` arm: direct vendor MCPs enabled, Glean MCP disabled.

## Workflow

1. Confirm the working directory contains `scripts/glean_mcp_eval.py`.
2. If `eval.config.json` or `golden_prompts.tsv` are missing, create them from examples:

   ```bash
   cp config/eval.config.example.json eval.config.json
   cp prompts/golden_prompts.example.tsv golden_prompts.tsv
   ```

3. Help the user edit:
   - `eval.config.json`
   - `golden_prompts.tsv`

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

- Do not run an arm if preflight fails unless the user explicitly overrides.
- Keep prompt wording identical across arms.
- Tell users to run arms back-to-back after switching MCP setup.
- Remind users to use a tiny 1-2 prompt smoke test before a customer-facing run.
- Treat result zips as customer confidential.
