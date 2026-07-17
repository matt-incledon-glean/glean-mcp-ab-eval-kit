"""Host adapters for the Glean MCP A/B eval kit.

The kit's core (`glean_mcp_eval.py`) is host-agnostic: config, prompts, the blind
judge, aggregation, reporting, and packaging are shared. Everything host-specific —
how you launch a headless run and how you harvest per-run metrics — lives behind the
`HostAdapter` contract in `base.py`, with one module per host.
"""
