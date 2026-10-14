---
name: design-cost-report
description: Generate a client-ready HTML report of how many tokens, which Claude models, how many sub-agents, and how much API cost (USD or local currency) a Claude Code design session used. Use this whenever the user finishes a design, says the task/design is complete, asks "how much did this cost", "token usage", "usage report", "cost report for the client", "how many tokens did we use", or wants a billing/usage summary for one or more sessions — even if they don't say "report".
---

# Design Cost Report

Produces a self-contained HTML report (cost by model, token breakdown, main agent vs
sub-agents, sessions, design files produced) from Claude Code's own transcripts.
The work is done by a Python script, so generating the report costs **zero tokens**.

## How to run

The script lives next to this file: `scripts/generate_report.py`.
Run it from the project folder (the folder where the design was built).

| Situation | Command |
|---|---|
| The session that just finished (default) | `python3 <skill-dir>/scripts/generate_report.py` |
| A whole design spanning several sessions | `python3 <skill-dir>/scripts/generate_report.py --all-sessions` |
| Sessions since a date | `python3 <skill-dir>/scripts/generate_report.py --since 2026-10-01` |
| Specific session(s) | `... --session <id> --session <id2>` |
| Override names | `... --design-name "Hotel landing page" --client-name "Saffron Stays"` |

On Windows use `python` instead of `python3`. `<skill-dir>` is usually
`~/.claude/skills/design-cost-report` (personal) or `.claude/skills/design-cost-report` (project).

The report is written to `<project>/reports/ai-cost-<design>-<date>-<id>.html` and the
script prints a one-line summary (path, tokens, USD, models). Tell the user that line and
the file path. Do not re-read or re-summarise the HTML — the summary line is enough.

## Per-project settings

If the user mentions a client name, design name, currency, or markup, create or update
`<project>/.design-report.json` (all keys optional):

```json
{
  "design_name": "Boutique Hotel Landing Page",
  "client_name": "Saffron Stays",
  "studio_name": "Pixel Studio",
  "currency": "INR",
  "fx_rate": 84.0,
  "markup_percent": 0,
  "output_dir": "reports",
  "show_session_ids": false
}
```

`fx_rate` is how many units of `currency` equal 1 USD — ask the user for the rate they want
rather than guessing. `markup_percent` adds a "Billed (incl. X% service)" figure.

## Pricing

Prices come from `scripts/pricing.json` (USD per million tokens, taken from
https://platform.claude.com/docs/en/about-claude/pricing). If the report shows
"Not priced (add to pricing.json)", add that model id there using the official rates.

## Notes to pass on if asked

- On a Pro/Max subscription the figure is the API-equivalent value, not a charge.
- Sub-agent transcripts are included automatically.
- The "/cost" command in Claude Code shows the live session total; this report should be
  close to it but is computed independently from the transcript.
