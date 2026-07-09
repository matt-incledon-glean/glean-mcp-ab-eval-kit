---
description: Grade, aggregate, and package Glean MCP eval results
allowed-tools: Bash
---

You are helping finish a Glean MCP A/B Eval Kit run.

Ask for missing values:

1. Config path, default `eval.config.json`
2. Participant ID, or blank for all participants with paired results
3. Whether to run judge grading, default yes

If grading is requested and a participant ID is supplied:

```bash
python3 scripts/glean_mcp_eval.py grade --config <config> --participant-id <participant-id>
```

If grading is requested for all participants:

```bash
python3 scripts/glean_mcp_eval.py grade --config <config>
```

Then run:

```bash
python3 scripts/glean_mcp_eval.py report --config <config>
python3 scripts/glean_mcp_eval.py package --config <config>
```

Report paths for `aggregate_summary.md`, `aggregate_rows.csv`, `submission_manifest.json`, and `eval_submission.zip`.
