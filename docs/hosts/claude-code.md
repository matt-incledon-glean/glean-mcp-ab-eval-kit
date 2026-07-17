# Running the eval on Claude Code

Claude Code is the reference host and the default (`"host": "claude-code"`). The
[README quick start](../../README.md#quick-start) is written for it end to end, so
this page only notes the host-specific details.

## Prerequisites

- **Claude Code** installed and on PATH. Verify: `claude --version`, then
  `python3 scripts/glean_mcp_eval.py doctor --config eval.config.json` (reports the
  version and whether the kit's required CLI flags are supported).
- **Python 3** (no packages required).

## Host-specific behavior

- **Launch**: each prompt runs as `claude -p "<prompt>" --output-format json …`.
- **Per-arm isolation**: `--mcp-config <arm file> --strict-mcp-config` — the arm sees
  only its own MCP servers regardless of what's installed globally.
- **Read-only gating**: `--allowedTools` / `--disallowedTools` (deny wins).
- **Usage**: harvested from Claude Code's local JSONL transcript under
  `~/.claude/projects/**` — measured, not estimated.
- **Cost**: `total_cost_usd` from the `-p` JSON result (host-reported), plus the
  list-price-normalized `computed_cost_usd`.
- **Judge**: `--json-schema` enforces the structured grade. This host is the default
  `judge_host` for every eval, including ones whose arms run on another host.

## Capabilities

| Per-arm isolation | Read-only gating | Per-run tokens | Reported cost | Structured judge |
|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ |

See [cursor.md](cursor.md) for the Cursor host, and [METHODOLOGY.md](../METHODOLOGY.md)
for the shared evaluation design.
