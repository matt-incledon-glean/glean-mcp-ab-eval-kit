# Field runbook: running a Glean MCP vs direct MCP eval with a customer

Audience: AE, AISM, AIOM, SA, or other Glean field team member helping a customer run a lightweight Glean MCP vs direct MCP eval.

Use customer-specific names, prompts, and connector lists only in that customer's private working copy. Keep shared templates customer-agnostic.

## 0. What this eval answers

The eval answers one practical question:

> In Claude Code, does using **Glean MCP** reduce token/cost consumption versus enabling the equivalent **direct vendor MCPs**, while preserving answer quality?

It does **not** test Glean calling third-party MCPs. It tests two retrieval paths in Claude:

1. Claude → Glean MCP → Glean knowledge graph / indexed customer corpus
2. Claude → vendor MCPs directly → Slack/Jira/Google Drive/etc.

## 1. Roles

### Glean field owner

Owns the process, config, and final readout.

### Customer technical owner

Can configure Claude Code MCP servers and confirm which systems are in scope.

### Test users

Run both arms of the eval using the same prompt set.

### Optional Glean support / TSE

Monitors connector health for Glean-indexed systems during the eval window.

## 2. Minimal timeline

### Day 0: Align scope, 30-45 minutes

Agree on:

- customer host: Claude Code
- arms: Glean MCP vs direct vendor MCPs
- model to hold constant
- systems/connectors in scope
- 5-10 golden prompts
- 3-5 pilot users, or more if available

### Day 1: Setup and smoke test, 30-60 minutes

- Install/configure MCPs in Claude Code.
- Configure this eval kit.
- Run one prompt in both arms with one test participant.
- Confirm tokens, answers, and report files generate.

### Days 2-5: Pilot runs

- Each user runs both arms back-to-back.
- Field owner collects packaged results.

### Final: Readout, 30 minutes

- Review aggregate summary.
- Exclude invalid rows.
- Spot-check quality.
- Present token/cost savings and quality gate.

## 3. Customer prerequisites

The customer needs:

- Claude Code installed and working.
- Ability to run `claude -p` from a terminal.
- Glean MCP configured in Claude Code.
- Direct vendor MCPs configured in Claude Code for the comparison arm.
- Python 3 installed. No Python packages are required.
- Permission to run prompts that may retrieve internal customer information.

## 4. Glean-side prerequisites

Before the eval:

- Confirm Glean has healthy connectors for the systems in scope.
- Confirm target documents/messages/tickets are searchable in Glean.
- Ask support/TSE to monitor connector health during the eval window if this is a strategic account.
- Document any asymmetry between Glean-indexed systems and direct MCP systems.

## 5. Pick the systems in scope

Start with the smallest useful set.

Common choices:

- Slack
- Jira / Confluence
- Google Drive or Microsoft 365
- Asana / Linear / GitHub, if relevant
- Zoom / meeting transcripts, if relevant

For an example customer, a hypothetical initial scope might be:

- Glean MCP
- Slack MCP
- Atlassian MCP
- Google Drive MCP
- GitHub MCP

Only include systems that both arms can reasonably access.

## 6. Create golden prompts

Use 5-10 prompts for the first pilot.

Good prompts are:

- real customer tasks
- answerable from connected systems
- cross-tool enough to show retrieval differences
- stable during the eval window
- phrased exactly the same in both arms

Bad prompts are:

- generic questions Claude can answer from memory
- prompts requiring private data a test user cannot access
- prompts whose answer changes hour-by-hour
- prompts that only one arm can answer because only one arm has access

Prompt TSV format:

```tsv
ID	Dept	Prompt
ENG_001	Engineering	Summarize the status of [real project] across Jira, docs, and Slack. Include owner, risks, and next steps.
```

## 7. Prepare the eval kit

Open the folder:

```bash
cd /path/to/glean-mcp-ab-eval-kit
```

Choose one MCP setup mode, then create editable local files.

**Strict mode, recommended for clean benchmarks:** the eval uses `mcp/*.json` files as the source of truth and does not require manual MCP add/remove between arms.

```bash
cp config/eval.config.strict.example.json eval.config.json
cp prompts/golden_prompts.example.tsv golden_prompts.tsv
mkdir -p mcp
cp config/mcp.glean.example.json  mcp/glean.mcp.json
cp config/mcp.direct.example.json mcp/direct.mcp.json
```

**Ambient mode, easiest for local debugging:** the eval uses whatever appears in `claude mcp list`; users must manually isolate MCPs between arms.

```bash
cp config/eval.config.ambient.example.json eval.config.json
cp prompts/golden_prompts.example.tsv golden_prompts.tsv
```

Edit:

- `eval.config.json`
- `golden_prompts.tsv`
- `mcp/glean.mcp.json` and `mcp/direct.mcp.json` if using strict mode

## 8. Configure `eval.config.json`

Set the model:

```json
"model": "opus"
```

Set the prompt file:

```json
"prompts_file": "golden_prompts.tsv"
```

`config/eval.config.example.json` is the source of truth for arm structure — copy it and adapt. Set `mcp_mode` explicitly:

```json
"mcp_mode": "strict"
```

or:

```json
"mcp_mode": "ambient"
```

In strict mode, each arm should set `mcp_config` (per-arm isolation, see section 9), the real server names, and **read-only** tool lists. The shipped example uses `glean_default` (Glean) vs direct vendor MCPs:

```json
"glean": {
  "label": "Glean MCP",
  "mcp_config": "mcp/glean.mcp.json",
  "expected_mcp_servers": ["glean_default"],
  "forbidden_mcp_servers": ["atlassian", "slack", "jira", "confluence", "github", "notion", "google_drive", "gmail", "outlook", "zoom"],
  "allowed_tools": ["mcp__glean_default__search", "mcp__glean_default__read_document", "mcp__glean_default__chat"],
  "disallowed_tools": ["mcp__glean_default__run_tool", "mcp__glean_default__find_skills", "mcp__glean_default__read_skill_files"]
}
```

```json
"direct": {
  "label": "Atlassian (direct)",
  "mcp_config": "mcp/direct.mcp.json",
  "expected_mcp_servers": ["atlassian"],
  "forbidden_mcp_servers": ["glean_default", "glean"],
  "allowed_tools": ["mcp__atlassian__search", "mcp__atlassian__getJiraIssue", "mcp__atlassian__getConfluencePage"],
  "disallowed_tools": ["mcp__atlassian__addCommentToJiraIssue", "mcp__atlassian__editJiraIssue", "mcp__atlassian__createJiraIssue", "mcp__atlassian__transitionJiraIssue"]
}
```

Important: server and tool names must match the customer’s Claude Code MCP names. Run `claude mcp list` to confirm servers. In strict mode, also run `claude mcp get <server>` and mirror any required headers/auth shape into the corresponding `mcp/*.json` file. Keep `allowed_tools` limited to read/search tools while `disallowed_tools` blocks every write and any arbitrary-dispatch tool (e.g. Glean's `run_tool`) — a read-only eval must never mutate live systems.

```bash
claude mcp list
claude mcp get glean_default
```

The CLI also blocks local built-ins such as `Bash`, `Read`, `Write`, `WebSearch`, and `WebFetch` by default via `default_disallow_builtin_tools: true`.

## 9. Smoke-test before involving users

Run:

```bash
python3 scripts/glean_mcp_eval.py doctor --config eval.config.json
```

`doctor` now reports the MCP mode per arm, which MCP source will be used, prompt count, and strict-config diagnostics such as placeholder values or missing expected servers. The prompt TSV is validated strictly; malformed rows fail before any eval runs.

Then reduce `golden_prompts.tsv` to one harmless prompt and test both arms.

> **Arm isolation.** If each arm sets `mcp_config` (recommended), the kit passes
> `--mcp-config <file> --strict-mcp-config` and each arm runs with only its own
> servers automatically — you do **not** enable/disable MCPs by hand. The manual
> enable/disable steps below are only a fallback when per-arm `mcp_config` is not used.

### Arm 1: Glean

Fallback only (no per-arm `mcp_config`): in Claude Code, enable only Glean MCP and disable direct vendor MCPs.

Then run:

```bash
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm glean --live
python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm glean --participant-id smoke01
```

### Arm 2: Direct

Fallback only (no per-arm `mcp_config`): switch Claude Code MCP setup — disable Glean MCP, enable direct vendor MCPs.

Then run:

```bash
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm direct --live
python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm direct --participant-id smoke01
```

### Generate smoke-test report

```bash
python3 scripts/glean_mcp_eval.py report --config eval.config.json
```

Open:

```text
results/aggregate_summary.md
results/aggregate_rows.csv
```

`run` refuses to start unless the latest live preflight passed for that arm. Use `--force` only when intentionally debugging a broken setup.

If this works, restore the full prompt set.

## 10. Run the pilot with users

Give each participant:

- the eval kit folder or repo
- the completed `eval.config.json`
- the finalized `golden_prompts.tsv`
- a participant ID, e.g. `customer01`
- assigned order: Glean first or Direct first

Use a balanced order:

- half run Glean → Direct
- half run Direct → Glean

For each participant:

```bash
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm <arm> --live
python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm <arm> --participant-id <participant_id>
```

Then switch MCP setup and run the other arm.

## 11. Result handoff: how participant results get shared

There are two supported modes.

### Mode A: each participant packages and sends results

This is the simplest customer-friendly flow.

After a participant completes both arms, they run:

```bash
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

They send this file to the field owner / analysis owner through the customer-approved secure channel:

```text
results/eval_submission.zip
```

Examples of acceptable sharing channels depend on the customer: internal Slack/Teams upload, secure Google Drive/SharePoint folder, Box folder, or customer ticket attachment. Treat the zip as customer confidential because it can contain answer text and source references.

The central analysis owner imports each participant zip into their local copy of the kit:

```bash
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/customer01/eval_submission.zip
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/customer02/eval_submission.zip
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/customer03/eval_submission.zip
```

Then the owner runs central grading/reporting:

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

### Mode B: one facilitator runs everything on one machine

Use this only for a very small pilot or a live workshop. The facilitator collects results directly in one local `results/` folder and then runs:

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

## 12. Grade, report, package

If a participant is analyzing only their own run after both arms are complete:

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json --participant-id <participant_id>
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

If a central owner imported multiple participant zips, omit `--participant-id`:

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

Outputs:

```text
results/aggregate_summary.md
results/aggregate_rows.csv
results/submission_manifest.json
results/eval_submission.zip
```

## 13. Using the Claude Code skill instead of raw terminal commands

This repo includes a project skill:

```text
.claude/skills/glean-mcp-eval/SKILL.md
```

Use the skill when the field owner or customer wants Claude to guide them step-by-step instead of remembering commands.

### Start Claude Code from the kit folder

```bash
cd /path/to/glean-mcp-ab-eval-kit
claude
```

Inside Claude Code, invoke:

```text
/glean-mcp-eval
```

Then ask in plain English, for example:

```text
Help me set up this eval for a customer. I want Glean MCP vs Slack/Jira/GDrive/GitHub direct MCPs. Walk me through config, preflight, a smoke test, and packaging participant results.
```

The skill should guide the user through the same workflow:

1. Create or edit `eval.config.json`.
2. Create or edit `golden_prompts.tsv`.
3. Run `doctor`.
4. Run arm preflight.
5. Run each arm.
6. Package results.
7. Import participant zips if doing central analysis.
8. Grade/report/package final results.

The skill is best for guided execution. The CLI output remains the source of truth for metrics.

## 14. What to inspect before making claims

Open `results/aggregate_rows.csv` and check `validity_flags`.

Exclude or manually review rows with:

- `glean_run_failed`
- `direct_run_failed`
- `glean_no_mcp_retrieval`
- `direct_no_mcp_retrieval`
- `model_mismatch`

Spot-check several paired answers before claiming quality held constant.

## 15. Suggested customer talk track

> We will run the same prompts in Claude Code twice: once with Glean MCP, once with the direct vendor MCP stack. We’ll hold the model and prompt wording constant. The kit reads Claude’s own local usage records, so token numbers are not estimated. We’ll only count rows where both arms actually retrieved information and used the same model. The goal is to see whether Glean reduces token/cost overhead while maintaining answer quality.

## 16. Common issues

### `claude` command not found

Claude Code is not installed or not on PATH. Ask the customer to open Claude Code docs or their internal setup instructions.

### Preflight says expected MCP server is missing

- Strict mode: add the server to the arm's `mcp/*.json` file, or update `expected_mcp_servers` to the exact name in that file.
- Ambient mode: run `claude mcp list`, enable/add the missing server, or update `expected_mcp_servers` to match the actual server name.

### `claude mcp list` is connected, but strict preflight says no tools are available

Strict mode ignores the user/global server definition except for stored OAuth credentials. Compare the working user server to the strict file:

```bash
claude mcp get glean_default
cat mcp/glean.mcp.json
```

Mirror required URL/type/headers into `mcp/glean.mcp.json` or switch to ambient mode.

### Preflight says forbidden server found

- Strict mode: remove the wrong-arm server from the arm's `mcp/*.json` file.
- Ambient mode: disable/remove the wrong-arm MCP before running that arm.

### Prompt file validation failed

Fix the TSV so every row has the same tab-separated columns as the header. Expected minimum columns:

```text
ID<TAB>Dept<TAB>Prompt
```

### Rows show no retrieval

The model answered from memory or did not call tools. Use more specific prompts that require current internal sources, and ensure MCP tools are allowed. Live preflight now requires tool use from every expected server.

### Quality scores show `NOT RUN`

Run:

```bash
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
```

### Model mismatch

Both arms must use the same model. Update `model` in `eval.config.json` and rerun invalid rows.

## 17. Minimal customer instructions

If the customer is comfortable with terminal, this is the smallest instruction block:

```bash
cd /path/to/glean-mcp-ab-eval-kit
cp config/eval.config.strict.example.json eval.config.json
cp prompts/golden_prompts.example.tsv golden_prompts.tsv
mkdir -p mcp
cp config/mcp.glean.example.json  mcp/glean.mcp.json
cp config/mcp.direct.example.json mcp/direct.mcp.json
# Edit eval.config.json, golden_prompts.tsv, and mcp/*.json
python3 scripts/glean_mcp_eval.py doctor --config eval.config.json
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm glean --live
python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm glean --participant-id user01
python3 scripts/glean_mcp_eval.py preflight --config eval.config.json --arm direct --live
python3 scripts/glean_mcp_eval.py run --config eval.config.json --arm direct --participant-id user01
python3 scripts/glean_mcp_eval.py grade --config eval.config.json --participant-id user01
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```

Participant sends to the analysis owner:

```text
results/eval_submission.zip
```

Analysis owner imports participant zips and creates final aggregate:

```bash
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/user01/eval_submission.zip
python3 scripts/glean_mcp_eval.py import --config eval.config.json /path/to/user02/eval_submission.zip
python3 scripts/glean_mcp_eval.py grade --config eval.config.json
python3 scripts/glean_mcp_eval.py report --config eval.config.json
python3 scripts/glean_mcp_eval.py package --config eval.config.json
```
