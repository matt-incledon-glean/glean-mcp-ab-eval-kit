# Reverse-engineered design notes

These notes summarize the reusable pattern inferred from the customer-built pilot, sanitized for open-source distribution.

## What the original plugin did

The plugin's job was not to make Glean call third-party MCPs. It evaluated two retrieval paths in Claude Code:

1. **Glean MCP path**: Claude uses Glean's knowledge graph / indexed enterprise corpus through one Glean MCP server.
2. **Vendor-direct path**: Claude uses several vendor MCP servers directly for the same underlying systems.

The plugin wrapped the test so end users did not need to manage files or metrics manually.

## End-to-end flow

1. **Tester chooses the current arm**
   - Glean arm: Glean MCP on; direct/vendor MCPs off.
   - Direct arm: Glean MCP off; vendor MCPs on.

2. **Preflight gates the run**
   - Checks expected MCP servers are configured.
   - Checks forbidden/wrong-arm servers are not configured.
   - Optionally makes a harmless live retrieval call through the arm's tools.
   - Stops before prompt execution on failure.

3. **Golden prompts run in clean contexts**
   - Fixed prompt TSV.
   - Same wording in both arms.
   - Same model in both arms.
   - One fresh Claude Code headless session per prompt.

4. **Usage is harvested from Claude records**
   - Reads Claude Code JSONL transcripts under `~/.claude/projects`.
   - Sums actual usage fields by billing tier:
     - input
     - output
     - cache creation/write
     - cache read
   - Captures model and tool-call evidence.

5. **Rows are validity-flagged**
   - setup failure
   - wrong/missing MCP servers
   - model mismatch
   - no retrieval/tool call
   - Claude CLI error

6. **Quality is judged centrally**
   - Paired answer comparison.
   - Completeness and groundedness on a 1-5 scale.
   - Winner labels: Glean, Direct, Tie.
   - Automated grading should be spot-checked before executive claims.

7. **Submission is tamper-evident**
   - Results, preflight records, raw Claude outputs, parsed usage, and grades are packaged in one zip.
   - Manifest includes SHA-256 checksums for every file.

## Why this is defensible

- **Within-subject crossover**: every participant is their own control.
- **Same prompts**: no prompt wording drift between arms.
- **Same model**: model mismatch is flagged.
- **Fresh sessions**: no prompt-to-prompt carryover.
- **Actual token records**: usage comes from Claude's transcript usage fields, not estimates or self-reporting.
- **Retrieval verified**: rows with zero tool calls are flagged.
- **Equivalent systems**: the direct arm should expose the same systems Glean indexes; exceptions must be documented.

## What this kit intentionally generalizes

- Customer-specific prompts are replaced by a TSV template.
- Customer-specific vendor server names are configurable.
- Pricing is configurable and should be updated by the evaluator.
- Glean-side connector health checks are documented as a process, not hard-coded to internal systems.
