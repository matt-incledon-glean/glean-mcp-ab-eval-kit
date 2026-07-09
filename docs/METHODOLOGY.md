# Methodology

## Evaluation question

Does routing enterprise retrieval through Glean MCP materially reduce Claude token consumption / list-price equivalent cost versus the equivalent set of direct vendor MCP connectors, without degrading answer quality?

## Design

Use a within-subject crossover:

- Every participant runs both arms.
- Half run Glean first, half run Direct first.
- Arms are run back-to-back to keep the accessible corpus stable.
- Each prompt runs in a fresh Claude Code headless session so one prompt cannot inherit another prompt's retrieved context.

## Arms

- **Glean arm**: Glean MCP enabled; direct vendor MCPs disabled.
- **Direct arm**: vendor MCPs enabled; Glean MCP disabled.

The vendor-direct arm should expose the same systems that Glean indexes for the evaluation. Document any asymmetry.

## Metrics

### Efficiency

Token usage is parsed from Claude Code JSONL transcripts:

- `input_tokens`
- `output_tokens`
- `cache_creation_input_tokens`
- `cache_read_input_tokens`

The kit also retains unknown usage fields for forward compatibility.

### Cost

Cost is computed from configurable per-million-token rates. Treat dollars as list-price equivalent, not subscription billing truth. The primary defensible metric is the token/cost ratio between arms under the same model.

### Quality

A judge model can compare paired answers using:

- completeness: did it cover the full request?
- groundedness: did it cite/source claims and avoid unsupported assertions?
- usefulness: is the answer ready to use?
- overall winner: quality first, efficiency second only when quality is comparable

Automated judging is a first-pass screen. For executive claims, spot-check with human reviewers.

## Validity checks

The kit records:

- preflight results
- configured MCP servers found locally
- live preflight probe result, if enabled
- model(s) observed in transcript
- tool calls by MCP server
- whether retrieval was attempted
- run errors

Exclude rows with failed setup, model mismatch, or zero retrieval unless there is a documented reason.

## Caveats

- Claude Code internals and transcript schemas may change. The parser is defensive but should be validated on a dry run.
- Direct vendor MCPs may load more tool schema/context than Glean MCP. That overhead is part of the real comparison if customers would otherwise run those servers directly.
- Small pilots are directional. Use confidence intervals / bootstrap analysis before company-wide claims.
- Quality judging can consume tokens and may itself be biased; retain raw paired answers for audit.
