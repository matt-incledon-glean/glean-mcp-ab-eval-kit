# Glean MCP A/B Eval Kit

Open-sourceable kit for running a defensible A/B evaluation of **Glean MCP** vs **vendor-direct MCP connectors** in Claude Code.

The kit is modeled after an enterprise crossover pilot pattern:

- **Arm A / Glean**: Claude Code with Glean MCP enabled.
- **Arm B / Direct**: Claude Code with the equivalent vendor MCPs enabled directly.
- Same model, same prompt set, same participant machine.
- Each prompt runs in a fresh Claude Code headless session.
- Usage is harvested from Claude Code's local JSONL transcripts, not estimated.
- Rows are auto-flagged for setup failures, model mismatch, and zero retrieval/tool calls.
- Results can be graded, aggregated, and packaged with checksums for central analysis.

> This repository does **not** ship customer-specific prompts or connector credentials. Customers provide their own MCP configs and golden prompt TSV.

## Repository layout

```text
.claude-plugin/plugin.json       Claude Code plugin manifest
commands/                       Plugin slash-command prompts
.claude/skills/glean-mcp-eval/  Project skill alternative to plugin commands
scripts/glean_mcp_eval.py       Dependency-free Python CLI
bin/glean-mcp-eval              Shell wrapper for zip installs
config/eval.config.example.json Example customer config
prompts/golden_prompts.example.tsv
                              Prompt TSV schema + safe sample prompts
docs/METHODOLOGY.md             Evaluation design and caveats
docs/CONNECTOR_HEALTH_CHECKLIST.md
                              Daily connector health process
docs/FIELD_RUNBOOK.md           Minimal field/customer runbook
docs/READOUT_TEMPLATE.md        Stakeholder readout template
docs/OPEN_SOURCE_NOTES.md       Sanitization checklist before publishing
```

## Quick start

### 1. Install / enable the Claude Code plugin

From the repo root in Claude Code:

```text
/plugin install .
/reload-plugins
```

If distributing as a zip, unzip it and install from that local path.

### 2. Copy and customize config

```bash
cp config/eval.config.example.json eval.config.json
cp prompts/golden_prompts.example.tsv golden_prompts.tsv
```

Edit `eval.config.json`:

- Set `prompts_file`.
- Set the model name you want held constant.
- Define `arms.glean.expected_mcp_servers` and `arms.direct.expected_mcp_servers`.
- Define `forbidden_mcp_servers` for each arm.
- Optionally set `allowed_tools`, `preflight_prompt`, and pricing.

### 3. Run preflight for the current arm

```bash
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm glean --live
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm direct --live
```

For zip installs you can use the wrapper instead:

```bash
bin/glean-mcp-eval preflight --config eval.config.json --arm glean --live
```

Preflight checks static MCP config and, with `--live`, runs a harmless Claude Code probe that should call the configured retrieval tools.

### 4. Run an arm

Each prompt is run in an isolated `claude -p` session and stored under `results/<participant>/<arm>/<prompt_id>/`.

```bash
python3 scripts/glean_mcp_eval.py run \
  --config eval.config.json \
  --arm glean \
  --participant-id user01

python3 scripts/glean_mcp_eval.py run \
  --config eval.config.json \
  --arm direct \
  --participant-id user01
```

Use a crossover schedule: half the testers run `glean → direct`, half run `direct → glean`.

### 5. Grade, report, and package

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json --participant-id user01
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

For central analysis, participants send `results/eval_submission.zip`. The analysis owner imports each zip, then runs aggregate grading/reporting:

```bash
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/user01/eval_submission.zip
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/user02/eval_submission.zip
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

Outputs:

- `results/aggregate_summary.md`
- `results/aggregate_rows.csv`
- `results/submission_manifest.json`
- `results/eval_submission.zip`

## Field runbook

For AE/AISM/AIOM/SA usage, start with [docs/FIELD_RUNBOOK.md](docs/FIELD_RUNBOOK.md).

## Plugin commands

After installing the plugin, use:

```text
/glean-mcp-eval:preflight
/glean-mcp-eval:run-arm
/glean-mcp-eval:grade-report-package
```

The slash commands guide Claude to invoke the local CLI with the right checks and prompts.

## Skill alternative

This repo also includes a project skill at `.claude/skills/glean-mcp-eval/SKILL.md`. In Claude Code, invoke it with:

```text
/glean-mcp-eval
```

Use the skill when you want a lightweight project-local workflow. Use the plugin when you want a versioned installable bundle with namespaced commands.

## What is measured

Per prompt / arm:

- input tokens
- output tokens
- cache creation/write tokens
- cache read tokens
- total tokens
- configured list-price equivalent cost
- model(s) observed in transcript
- MCP tool calls by server
- retrieval-attempted flag
- final answer text
- optional judge scores: completeness, groundedness, usefulness, winner

## Validity gates

Rows are flagged or excluded when:

- expected MCP servers are missing
- forbidden MCP servers are configured in the wrong arm
- live preflight fails
- observed model differs across arms
- no MCP retrieval/tool call was observed
- `claude -p` returned an error

## Security / privacy

This kit records final answers and local transcript-derived metadata. Do not publish customer results. Before open sourcing this repo, verify that only generic sample prompts/configs are included.

## License

Suggested: Apache-2.0. Add `LICENSE` before public release.
