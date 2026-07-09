# Connector health checklist

Run this before and during the eval window. The goal is to avoid confusing Glean-vs-direct retrieval differences with stale or broken connector state.

## Before prompt finalization

- [ ] List the enterprise systems each golden prompt is expected to use.
- [ ] Confirm Glean indexes those systems.
- [ ] Confirm the direct MCP arm exposes the same systems, or document asymmetry.
- [ ] Choose prompts with verifiable answers in the connected systems.
- [ ] Avoid prompts whose answer is expected to change during the eval window unless freshness is the point of the test.

## Before each eval day

For each in-scope Glean connector:

- [ ] Crawl/indexing status is healthy.
- [ ] Recent incremental crawls have completed.
- [ ] Error rates are normal.
- [ ] Permissions sync is healthy.
- [ ] Known high-value source docs/messages/tickets are searchable in Glean.

For each direct MCP connector:

- [ ] Server is configured in Claude Code.
- [ ] OAuth/token auth is valid for the tester.
- [ ] A harmless read-only query succeeds.
- [ ] Tool list loads without errors.

## During participant runs

- [ ] Participant has the correct arm enabled.
- [ ] Wrong-arm MCP servers are disabled.
- [ ] `preflight --live` passes.
- [ ] Same model is selected for both arms.
- [ ] Both arms are run close together in time.

## After runs

- [ ] Review `results/_preflight/**/preflight.json`.
- [ ] Review `validity_flags` in `aggregate_rows.csv`.
- [ ] Exclude failed setup, no-retrieval, or model-mismatch rows from headline claims.
- [ ] Preserve raw result zips for audit.
