# Running the eval on Cursor

> **Status: skeleton.** The Cursor adapter (`scripts/hosts/cursor.py`) builds the
> right `cursor-agent` command, stages per-arm isolation, and parses `stream-json`.
> A few things need confirming on a live Cursor install — search the adapter for
> `TODO(verify)` and see [Open items](#open-items) below.

The eval methodology is identical to Claude Code (same crossover design, same golden
prompts, same blind judge, same aggregation). Only *how a run is launched and
measured* differs. See [METHODOLOGY.md](../METHODOLOGY.md) for the shared design and
[claude-code.md](claude-code.md) for the reference host.

## Prerequisites

- **Cursor CLI** (`cursor-agent`) installed and on PATH. Verify: `cursor-agent --version`.
- **Auth**: `export CURSOR_API_KEY=...` (or pass `--api-key`).
- **Python 3** (no packages required).

## 1. Configure

```bash
cp config/eval.config.example.json eval.config.json
cp prompts/golden_prompts.example.tsv golden_prompts.tsv
mkdir -p mcp
cp config/mcp.glean.example.json    mcp/glean.mcp.json      # Cursor-shape server entries (see note)
cp config/mcp.cursor.example.json   mcp/direct.mcp.json
```

In `eval.config.json` set the host:

```json
"host": "cursor",
"judge_host": "claude-code"
```

- `host: "cursor"` runs the **arms** on Cursor.
- `judge_host: "claude-code"` keeps the **judge** on a structured-output-capable host
  so quality scores stay comparable across hosts. If the graders only have Cursor,
  set `judge_host: "cursor"` and the kit falls back to prompt-and-parse JSON (less
  reliable). You can also grade on a different machine.

**MCP server-entry shape differs from Claude.** Cursor's `.cursor/mcp.json` uses
`{"url": ...}` (remote) or `{"command", "args"}` (local), not Claude's
`{"type","url","headers"}`. Point each arm's `mcp_config` at a Cursor-shaped file
(see `config/mcp.cursor.example.json`). The adapter stages that file's `mcpServers`
into a per-arm workspace and runs `cursor-agent --workspace <that dir>`, so each arm
sees only its own servers.

Keep `allowed_tools` / `disallowed_tools` read-only — the adapter translates them into
a `.cursor/cli.json` permissions block (`Mcp(server:tool)` allow-list, `Write`/`Shell`
denied; deny wins).

## 2. Preview the exact commands (no tokens)

```bash
python3 scripts/glean_mcp_eval.py doctor   --config eval.config.json --host cursor
python3 scripts/glean_mcp_eval.py run      --config eval.config.json --host cursor --arm glean  --participant-id user01 --dry-run
```

`--dry-run` prints the exact `cursor-agent` invocation without executing — good for a
security review.

## 3. Run, grade, report

Same commands as any host (the `run` reads `host` from config, or pass `--host cursor`):

```bash
python3 scripts/glean_mcp_eval.py run    --config eval.config.json --arm glean  --participant-id user01
python3 scripts/glean_mcp_eval.py run    --config eval.config.json --arm direct --participant-id user01
python3 scripts/glean_mcp_eval.py grade  --config eval.config.json --participant-id user01   # judge runs on judge_host
python3 scripts/glean_mcp_eval.py report --config eval.config.json
```

## What Cursor can and cannot measure

| Metric | Cursor | Note |
|---|---|---|
| Answer + quality (judge) | ✅ | Judge runs on `judge_host`; Cursor answers are graded blind like any host |
| Latency | ✅ | `duration_ms` from the `stream-json` result event |
| Model pinning / reported | ✅ / ⚠️ | `--model` pins; served model comes from the `stream-json` system event |
| Per-arm MCP isolation | ✅ | Per-arm `--workspace` + staged `.cursor/mcp.json` |
| Read-only tool gating | ✅ | `.cursor/cli.json` permissions (deny wins) |
| Per-run **token usage** | ⚠️ | Parsed from `stream-json`; field is version-dependent — **verify** (below) |
| Per-run **$ cost** | ❌ | Cursor exposes no per-run cost — the kit's **list-price-normalized** `computed_cost_usd` is the cross-host cost metric; `reported_cost` is null |
| Structured judge output | ❌ | No JSON-schema enforcement — that's why the judge runs on `judge_host` |

**Cross-host cost note:** because Cursor gives no vendor cost, compare hosts on the
**list-price-normalized cost** (same `pricing_per_million` rate card applied to both)
plus marginal tokens and latency — not on any vendor-reported dollar figure.

## Open items (`TODO(verify)` in `scripts/hosts/cursor.py`)

1. **Token-usage field** — confirm `cursor-agent`'s `stream-json` (or JSON) emits per-run
   token counts on your pinned CLI version, and that `_extract_usage()` maps them
   correctly. If not, drive Cursor via the TypeScript SDK (`RunResult.usage`) through a
   small Node helper, or accept latency+quality-only for the Cursor arm.
2. **Tool-call event shape** — confirm the `tool_call` event field names so
   `mcp_servers_used` / `retrieval_attempted` populate (used by the `no_retrieval`
   validity gate).
3. **Permission rule grammar** — confirm `.cursor/cli.json` accepts the
   `Mcp(server:tool)` / `Write(**)` / `Shell(**)` rules the adapter writes.
4. **MCP entry shape** — confirm your Cursor-shaped `mcp/*.json` server entries load
   under `--workspace`.

Pin a `cursor-agent` version once these are confirmed and note it here.
