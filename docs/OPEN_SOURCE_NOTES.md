# Open-source release checklist

Before publishing:

- [ ] Remove all customer names, prompts, answers, transcripts, URLs, and screenshots.
- [ ] Keep only generic sample prompt templates.
- [ ] Confirm no secrets in `.mcp.json`, `eval.config.json`, transcripts, or results.
- [ ] Add a real `LICENSE` file.
- [ ] Decide whether `pricing_per_million` defaults should be omitted or clearly marked as examples.
- [ ] Test on macOS and Linux with a fresh Claude Code install.
- [ ] Confirm plugin install path and command namespace on current Claude Code release.
- [ ] Add a note that customers must comply with Anthropic, Glean, and vendor MCP terms.
