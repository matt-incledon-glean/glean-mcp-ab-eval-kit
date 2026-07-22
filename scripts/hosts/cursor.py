"""Cursor host adapter (SKELETON).

Runs one prompt headless via Cursor's `cursor-agent` CLI and harvests per-run
metrics. The design is settled; the spots that need a live Cursor to confirm are
marked `TODO(verify)`. See docs/hosts/cursor.md.

Key differences from Claude Code (from Cursor docs, 2026-07):
  - Command: `cursor-agent -p "<prompt>" --output-format stream-json --force --trust`.
  - Isolation: no `--strict-mcp-config` flag, and cursor-agent merges the global
    ~/.cursor/mcp.json + installed plugins into every workspace, so a per-arm
    `.cursor/mcp.json` can only *add* this arm's server. Real isolation is
    enforced by staging Cursor's per-project `mcp-disabled.json` (an array of
    runtime server ids) so every non-sanctioned server — including plugin
    servers, which cli.json Mcp() deny does NOT gate under --force — is not
    loaded. `.cursor/cli.json` still gates tools (read-only floor).
  - Cost: NOT exposed by Cursor — `reported_cost_usd` is always None; the kit's
    list-price-normalized `computed_cost_usd` is the cross-host cost metric.
  - Token usage: available via the TypeScript SDK for certain; via CLI JSON it is
    version-dependent and not yet in the published schema. We parse `stream-json`
    best-effort and leave a TODO to confirm the field on the pinned CLI version.
  - Structured output: no JSON-schema enforcement, so run the JUDGE on a
    structured-output-capable host (config `judge_host`, default claude-code).
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import HostAdapter, register

# Cursor usage field names -> our canonical USAGE_KEYS. TODO(verify) against the
# pinned cursor-agent version; the CLI JSON usage shape is not yet documented.
_USAGE_ALIASES = {
    "input_tokens": ("inputTokens", "input", "input_tokens", "prompt_tokens"),
    "output_tokens": ("outputTokens", "output", "output_tokens", "completion_tokens"),
    "cache_creation_input_tokens": ("cacheWriteTokens", "cache_write", "cacheCreationInputTokens"),
    "cache_read_input_tokens": ("cacheReadTokens", "cache_read", "cacheReadInputTokens"),
}


def _cursor_project_slug(path: Path) -> str:
    """Return Cursor CLI's filesystem-safe project slug for an absolute path.

    Cursor derives the ~/.cursor/projects/<slug> namespace by replacing every run
    of non-alphanumeric characters with a single '-' and trimming leading/
    trailing '-'. e.g. '/private/tmp/x/_cursor_ws' -> 'private-tmp-x-cursor-ws'.
    Matching this exactly matters: the OAuth/approval state and mcp-disabled.json
    we stage are only read if they land in the namespace Cursor actually uses.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "-", str(path.resolve())).strip("-")


def _load_arm_servers(root: Path, arm_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Read this arm's mcp_config file and return its mcpServers mapping.

    TODO(verify): Cursor's `.cursor/mcp.json` server-entry shape may differ from
    Claude's (Claude: {"type","url","headers"}; Cursor remote: {"url": ...} or
    {"command","args"}). For a Cursor arm, point mcp_config at a Cursor-shaped
    file (see config/mcp.cursor.example.json). We stage the entries as-is.
    """
    mcp_config = arm_cfg.get("mcp_config")
    if not mcp_config:
        return {}
    p = Path(mcp_config)
    if not p.is_absolute():
        p = root / p
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    servers = data.get("mcpServers")
    return servers if isinstance(servers, dict) else {}


def _norm_server(name: str) -> str:
    """Match the core's normalize_server_name so adapter deny rules and the
    reporting-side validity check agree on server identity."""
    return re.sub(r"[^a-z0-9_-]+", "", str(name).lower().strip())


def _discover_available_servers(cursor_home: Path) -> Dict[str, str]:
    """Best-effort {runtime_server_id: normalized_id} for every MCP server
    cursor-agent will merge into a workspace.

    cursor-agent has no --strict-mcp-config flag, so an arm inherits (a) the
    global ~/.cursor/mcp.json servers and (b) every installed plugin's servers.
    A plugin server's runtime identifier is `plugin-<plugin.name>-<serverKey>`
    (verified against plugin-atlassian-atlassian and plugin-glean-vnext-glean).
    We enumerate both so callers can deny everything the arm is not supposed to
    touch, instead of maintaining a brittle hand-written forbidden list.
    """
    found: Dict[str, str] = {}
    base = cursor_home / ".cursor"
    try:
        data = json.loads((base / "mcp.json").read_text(encoding="utf-8"))
        for key in (data.get("mcpServers") or {}):
            found[key] = _norm_server(key)
    except Exception:
        pass
    plugins_dir = base / "plugins"
    if plugins_dir.is_dir():
        for plugin_json in plugins_dir.rglob("plugin.json"):
            try:
                pj = json.loads(plugin_json.read_text(encoding="utf-8"))
                pname = pj.get("name")
                if not pname:
                    continue
                # plugin.json lives under .cursor-plugin/ or .claude-plugin/;
                # the server manifest (.mcp.json) sits at the plugin root.
                for cand in (
                    plugin_json.parent / ".mcp.json",
                    plugin_json.parent.parent / ".mcp.json",
                ):
                    if not cand.exists():
                        continue
                    md = json.loads(cand.read_text(encoding="utf-8"))
                    for skey in (md.get("mcpServers") or {}):
                        rid = f"plugin-{pname}-{skey}"
                        found[rid] = _norm_server(rid)
                    break
            except Exception:
                continue
    return found


def _permissions_from_arm(arm_cfg: Dict[str, Any]) -> Dict[str, List[str]]:
    """Translate the kit's allowed_tools/disallowed_tools into a Cursor
    `.cursor/cli.json` permissions block. Deny wins over allow.

    NOTE: this gates *tools* (read-only floor + specific write tools). It does
    NOT enforce server isolation: live testing showed cursor-agent honors
    cli.json Mcp() deny rules for mcp.json servers but NOT for plugin-provided
    servers under --force. Server isolation is done separately by staging an
    `mcp-disabled.json` into the run's project namespace (see prepare()).

    TODO(verify): confirm the exact rule grammar Cursor accepts. Docs show
    `Mcp(server:tool)`, `Write(...)`, `Shell(...)`, `Read(...)` with `*`. We
    translate `mcp__<server>__<tool>` -> `Mcp(<server>:<tool>)` and always deny
    Write/Shell for a read-only eval.
    """
    def to_rule(tool: str) -> Optional[str]:
        if tool.startswith("mcp__"):
            parts = tool.split("__")
            if len(parts) >= 3:
                return f"Mcp({parts[1]}:{parts[2]})"
            if len(parts) == 2:
                return f"Mcp({parts[1]}:*)"
        return tool  # pass through non-mcp rules verbatim

    allow = [r for r in (to_rule(t) for t in (arm_cfg.get("allowed_tools") or [])) if r]
    deny = [r for r in (to_rule(t) for t in (arm_cfg.get("disallowed_tools") or [])) if r]
    # Read-only floor: never allow writes or shell during an eval run.
    for hard in ("Write(**)", "Shell(**)"):
        if hard not in deny:
            deny.append(hard)
    return {"allow": allow, "deny": deny}


def _servers_to_disable(arm_cfg: Dict[str, Any], discovered: Dict[str, str]) -> List[str]:
    """Return the runtime server ids to disable for this arm: every discovered
    server (global mcp.json + plugins) whose normalized id is not one of the
    arm's sanctioned servers. Sanctioned = expected_mcp_servers UNION
    require_live_tool_servers, so an arm may reach its target via either the
    workspace mcp.json server or an equivalent plugin. This is what actually
    enforces arm isolation on Cursor, via a staged mcp-disabled.json.
    """
    keep = {
        _norm_server(x)
        for x in (
            list(arm_cfg.get("expected_mcp_servers") or [])
            + list(arm_cfg.get("require_live_tool_servers") or [])
        )
    }
    return sorted(rid for rid, norm in discovered.items() if norm not in keep)


def _extract_usage(obj: Any) -> Dict[str, int]:
    """Best-effort pull of the four canonical token counts from a Cursor result
    object. Handles a flat `usage` map and a nested `tokens.cache.{read,write}`
    shape. TODO(verify) on the pinned CLI version."""
    usage = {k: 0 for k in _USAGE_ALIASES}
    if not isinstance(obj, dict):
        return usage
    src = obj.get("usage") or obj.get("tokens") or {}
    if not isinstance(src, dict):
        return usage
    cache = src.get("cache") if isinstance(src.get("cache"), dict) else {}
    for canonical, aliases in _USAGE_ALIASES.items():
        for a in aliases:
            if isinstance(src.get(a), (int, float)):
                usage[canonical] = int(src[a])
                break
        else:
            if canonical == "cache_read_input_tokens" and isinstance(cache.get("read"), (int, float)):
                usage[canonical] = int(cache["read"])
            elif canonical == "cache_creation_input_tokens" and isinstance(cache.get("write"), (int, float)):
                usage[canonical] = int(cache["write"])
    return usage


class CursorAdapter(HostAdapter):
    name = "cursor"
    caps = {
        "per_arm_isolation": True,       # via per-arm --workspace + staged .cursor/mcp.json
        "readonly_gating": True,         # via .cursor/cli.json permissions (deny wins)
        "per_run_token_usage": True,     # via stream-json / SDK — TODO(verify) on CLI version
        "reported_cost": False,          # Cursor does not expose per-run cost
        "structured_output": False,      # no JSON-schema enforcement; judge elsewhere
    }

    def executable_present(self) -> bool:
        return shutil.which("cursor-agent") is not None

    def build_command(
        self,
        root: Path,
        cfg: Dict[str, Any],
        arm_cfg: Dict[str, Any],
        prompt: str,
        out_dir: Path,
        *,
        model_key: str = "model",
        max_turns: Optional[int] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[str], Dict[str, Any]]:
        ws = out_dir / "_cursor_ws"
        cmd: List[str] = [
            "cursor-agent", "-p", prompt,
            "--output-format", "stream-json",  # per-event; lets us capture model + usage + tool calls
            "--force", "--trust",              # fully unattended (no approval / trust prompts)
            "--workspace", str(ws),
        ]
        model = cfg.get(model_key) or cfg.get("model")
        if model:
            cmd.extend(["--model", str(model)])
        # NOTE: cursor-agent has no documented --max-turns / step-limit flag; the
        # `max_turns` arg is intentionally ignored. json_schema is NOT enforced by
        # Cursor — the judge should run on a structured-output host (judge_host).
        extra = [str(x) for x in (cfg.get("extra_cursor_args") or [])]
        discovered = _discover_available_servers(Path.home())
        disabled_servers = _servers_to_disable(arm_cfg, discovered)
        # Guard: --approve-mcps force-approves EVERY merged server (global
        # mcp.json + all plugins), which overrides the per-project
        # mcp-disabled.json and silently re-contaminates the arm (verified live:
        # the direct arm reached glean_default on every prompt with this flag).
        # Drop it whenever we are isolating servers so isolation stays authoritative.
        if disabled_servers and "--approve-mcps" in extra:
            sys.stderr.write(
                "[cursor] dropping --approve-mcps: it defeats mcp-disabled.json "
                "server isolation. Unattended approval is handled by --force plus "
                "staged mcp-approvals.json.\n"
            )
            extra = [x for x in extra if x != "--approve-mcps"]
        cmd.extend(extra)
        ctx = {
            "cwd": str(ws),
            "ws": str(ws),
            "servers": _load_arm_servers(root, arm_cfg),
            "permissions": _permissions_from_arm(arm_cfg),
            # Runtime server ids to disable for this arm (global mcp.json +
            # plugin servers that are not this arm's sanctioned server). Staged
            # as mcp-disabled.json in prepare() — the only mechanism that
            # reliably keeps plugin servers out of the run.
            "disabled_servers": disabled_servers,
            # Cursor stores MCP OAuth tokens/approvals under a project-path
            # namespace. The eval workspace is intentionally isolated, so stage
            # the already-authenticated local state into that namespace rather
            # than putting credentials in the repo or MCP config.
            "auth_source_dir": str(
                Path.home() / ".cursor" / "projects" / _cursor_project_slug(root)
            ),
            "raw_output_path": str(out_dir / "cursor_output.json"),
        }
        return cmd, ctx

    def prepare(self, ctx: Dict[str, Any]) -> None:
        ws = Path(ctx["ws"])
        cdir = ws / ".cursor"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "mcp.json").write_text(
            json.dumps({"mcpServers": ctx.get("servers", {})}, indent=2), encoding="utf-8"
        )
        (cdir / "cli.json").write_text(
            json.dumps({"permissions": ctx.get("permissions", {})}, indent=2), encoding="utf-8"
        )

        # OAuth state is kept outside the workspace under ~/.cursor/projects.
        # Copy only the auth metadata files into the isolated workspace's
        # project namespace; never write these secrets into the repository.
        source_dir = Path(ctx.get("auth_source_dir", ""))
        target_dir = Path.home() / ".cursor" / "projects" / _cursor_project_slug(ws)
        target_dir.mkdir(parents=True, exist_ok=True)
        if source_dir.is_dir():
            for filename in ("mcp-auth.json", "mcp-approvals.json"):
                source = source_dir / filename
                if source.exists():
                    shutil.copy2(source, target_dir / filename)

        # Server isolation: cursor-agent merges the global ~/.cursor/mcp.json and
        # every installed plugin into the run regardless of the workspace
        # mcp.json, and cli.json Mcp() deny rules do not gate plugin servers under
        # --force. The reliable lever is Cursor's per-project mcp-disabled.json
        # (an array of runtime server ids), which we stage into this run's
        # namespace so non-sanctioned servers "will no longer be loaded".
        disabled = list(ctx.get("disabled_servers") or [])
        (target_dir / "mcp-disabled.json").write_text(
            json.dumps(disabled, indent=2), encoding="utf-8"
        )

    def harvest(
        self,
        proc: Dict[str, Any],
        root: Path,
        out_dir: Path,
        cfg: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = []
        for line in (proc.get("stdout") or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue

        raw_path = ctx.get("raw_output_path") or str(out_dir / "cursor_output.json")
        Path(raw_path).write_text(json.dumps(events, indent=2), encoding="utf-8")

        model = None
        answer_text = ""
        duration_ms = None
        session_id = None
        is_error = False
        tool_calls: List[Dict[str, Any]] = []
        usage = {k: 0 for k in _USAGE_ALIASES}

        for ev in events:
            etype = ev.get("type")
            if etype == "system":
                model = ev.get("model") or model
                session_id = ev.get("session_id") or ev.get("sessionId") or session_id
            elif etype in ("tool_call", "tool_use"):
                # Cursor 2026.07 emits MCP calls nested under
                # tool_call.mcpToolCall.args, with the server and tool names in
                # serverIdentifier/providerIdentifier and toolName. Preserve the
                # canonical mcp__server__tool form used by the eval kit while
                # retaining generic tool-call events for diagnostics.
                envelope = ev.get("tool_call") or ev.get("toolCall") or {}
                mcp_call = envelope.get("mcpToolCall") if isinstance(envelope, dict) else None
                if isinstance(mcp_call, dict):
                    args = mcp_call.get("args") or {}
                    server = args.get("serverIdentifier") or args.get("providerIdentifier")
                    tool = args.get("toolName") or args.get("name")
                    name = f"mcp__{server}__{tool}" if server and tool else str(tool or "")
                else:
                    name = str(ev.get("name") or ev.get("tool") or "")
                    server = None
                    if name.startswith("mcp__"):
                        parts = name.split("__")
                        server = parts[1] if len(parts) >= 2 else None
                tool_calls.append({"name": name, "server": server})
            elif etype == "result":
                answer_text = ev.get("result") or answer_text
                duration_ms = ev.get("duration_ms") or duration_ms
                session_id = ev.get("session_id") or session_id
                is_error = bool(ev.get("is_error"))
                got = _extract_usage(ev)
                if any(got.values()):
                    usage = got

        mcp_servers_used: Dict[str, int] = {}
        for tc in tool_calls:
            if tc.get("server"):
                mcp_servers_used[tc["server"]] = mcp_servers_used.get(tc["server"], 0) + 1

        transcript = {
            "found": bool(events),
            "usage": usage,
            "unknown_usage": {},
            "models": {model: 1} if model else {},
            "tool_calls": tool_calls,
            "tool_call_count": len(tool_calls),
            "mcp_tool_call_count": sum(1 for tc in tool_calls if tc.get("server")),
            "mcp_servers_used": mcp_servers_used,
            "retrieval_attempted": bool(tool_calls),
            "errors": [] if events else ["no stream-json events parsed"],
        }
        return {
            "ok": proc.get("returncode") == 0 and not is_error,
            "session_id": session_id,
            "transcript": transcript,
            "usage": usage,
            "reported_cost_usd": None,  # Cursor does not expose per-run cost
            "duration_ms": duration_ms,
            "num_turns": None,
            "answer_text": answer_text,
            "raw_output_path": raw_path,
            "output_type": "cursor-stream-json",
            "output_subtype": "error" if is_error else "success",
        }

    def doctor(self, root: Path) -> Dict[str, Any]:
        present = self.executable_present()
        return {
            "cursor_agent_on_path": shutil.which("cursor-agent"),
            "caps": self.caps,
            "notes": [
                "Cursor does not expose per-run $ cost; list-price-normalized cost is used.",
                "TODO(verify): confirm token usage appears in stream-json on your cursor-agent version.",
                "Run the judge on a structured-output host via config 'judge_host' (default claude-code).",
            ] if present else ["cursor-agent not found on PATH"],
        }


register(CursorAdapter())
