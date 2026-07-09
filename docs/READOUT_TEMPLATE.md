# Stakeholder readout template

Use this after `python3 scripts/glean_mcp_eval.py report --config eval.config.json`.

## Purpose

Decide whether Glean MCP delivers material token/cost savings versus the equivalent direct MCP connector stack, without degrading answer quality.

## Test design

- Design: within-subject crossover A/B
- Participants: `[N]`
- Prompts per participant: `[N]`
- Arm A: Glean MCP
- Arm B: direct vendor MCPs `[list]`
- Model: `[model]`
- Valid paired rows: `[N]`
- Excluded rows and reasons: `[summary]`

## Headline

Glean MCP used **[X]% fewer configured-cost tokens / [Y]% lower list-price equivalent cost per task** than direct vendor MCPs, with **[no material change / a change]** in answer quality.

## Results

| Metric | Glean MCP | Direct MCP | Delta |
|---|---:|---:|---:|
| Avg tokens / task | `[x]` | `[y]` | `[delta]` |
| Avg configured cost / task | `$[x]` | `$[y]` | `$[delta]` |
| Completeness, 1-5 | `[x]` | `[y]` | `[delta]` |
| Groundedness, 1-5 | `[x]` | `[y]` | `[delta]` |
| Retrieval-attempted rate | `[x]%` | `[y]%` | `[delta]` |

## Quality gate

Savings count only if quality is comparable. Summarize:

- Overall winner counts: `[Glean / Direct / Tie]`
- Completeness winner counts: `[Glean / Direct / Tie]`
- Groundedness winner counts: `[Glean / Direct / Tie]`
- Human spot-check notes: `[notes]`

## Why this holds up

- Same participant ran both arms.
- Same prompt wording across arms.
- Same model across arms; mismatches excluded.
- Claude's own JSONL usage records used for token counts.
- Rows with no retrieval/tool call were flagged.
- Connector health was checked before/during the test.

## Caveats

- Pilot sample size is directional unless scaled.
- Dollars are list-price equivalent, not necessarily subscription billing.
- Automated grading should be spot-checked.
- Direct-arm tool schema overhead is part of the real-world comparison if users would otherwise enable those vendor MCPs directly.

## Decision rule

Adopt / expand Glean MCP if:

- Cost/token savings are material, e.g. `>= 15%`, and
- Quality is within noise or better, and
- Exclusions do not explain the observed result.

Re-run or scale the eval if the signal is directional but confidence is low.
