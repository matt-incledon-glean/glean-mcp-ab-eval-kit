---
description: Run one arm of the Glean MCP eval
allowed-tools: Bash
---

You are helping run one arm of the Glean MCP A/B Eval Kit.

Ask the user for missing values:

1. Config path, default `eval.config.json`
2. Arm, one of `glean` or `direct`
3. Participant ID, e.g. `user01`
4. Whether preflight already passed

If preflight has not passed, run preflight first:

```bash
python3 scripts/glean_mcp_eval.py preflight --config <config> --arm <arm> --live
```

If preflight passes, run:

```bash
python3 scripts/glean_mcp_eval.py run --config <config> --arm <arm> --participant-id <participant-id>
```

Summarize completed prompt count, failed prompt count, and results directory. Remind the user to switch MCP setup before running the other arm.
