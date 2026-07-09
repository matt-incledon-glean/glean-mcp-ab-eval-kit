---
description: Validate current Glean MCP eval arm setup
allowed-tools: Bash
---

You are helping run the Glean MCP A/B Eval Kit preflight.

Ask the user for these values if they were not provided in the command text:

1. Config path, default `eval.config.json`
2. Arm, one of `glean` or `direct`
3. Whether to run live preflight, default yes

Then run:

```bash
python3 scripts/glean_mcp_eval.py preflight --config <config> --arm <arm> --live
```

If the user declines live preflight, omit `--live`.

Report:

- PASS / FAIL
- missing expected MCP servers
- forbidden MCP servers found
- live tool-call evidence, if available
- exact next command to run the arm

Do not continue to `run` if preflight fails unless the user explicitly overrides.
