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

The judge is blinded to arm identity: answers are shown as "A"/"B" with a deterministic, auditable assignment (hash of participant + prompt), then de-blinded after grading. By default the judge also sees each answer's work-token count so it can break ties on efficiency. Because token counts can subtly **anchor** quality scores, set `judge_hide_tokens: true` in the config for a pure-quality pass that withholds them — running one efficiency-aware pass and one hidden-token pass and comparing is a cheap robustness check.

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
- Small pilots are directional. `report` prints a bootstrap 95% CI on the headline savings; treat a wide interval (small n) as "not yet significant" before company-wide claims.
- Showing token counts to the judge (even blinded to arm identity) can anchor quality scores. Run a `judge_hide_tokens: true` pass if you need quality judged independently of efficiency.
- The fair efficiency comparison is Glean MCP vs the **full set** of vendor MCPs a customer would otherwise run, not a single vendor: Glean carries the fixed per-session tool-schema cost of all its connectors, so a one-vendor arm understates Glean's consolidation benefit.
- A read-only eval must gate tools to read/search only. Arbitrary-dispatch tools (e.g. Glean's `run_tool`) and write tools must be denied, or an agent may mutate live systems while answering a read-only prompt.
- Quality judging can consume tokens and may itself be biased; retain raw paired answers for audit.
