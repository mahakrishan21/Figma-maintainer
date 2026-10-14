# Design Cost Report kit for Claude Code

Gives you an HTML report after every design: tokens used, models used, sub-agent runs,
and API cost (USD or your currency), ready to share with a client.

## What's inside
- `skills/design-cost-report/` – the skill (SKILL.md + Python script + pricing table)
- `agents/design-cost-reporter.md` – a sub-agent you can call: "use design-cost-reporter"
- `hooks/settings-snippet.json` – makes the report generate automatically when a session ends
- `example-report.html` – a sample report

## Install (macOS / Linux)
```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r skills/design-cost-report ~/.claude/skills/
cp agents/design-cost-reporter.md ~/.claude/agents/
```
Then merge `hooks/settings-snippet.json` into `~/.claude/settings.json`
(or run `/hooks` inside Claude Code and add a **SessionEnd** hook with that command).

## Install (Windows)
Copy the same folders into `%USERPROFILE%\.claude\skills` and `%USERPROFILE%\.claude\agents`.
In the hook command use:
`python %USERPROFILE%\.claude\skills\design-cost-report\scripts\generate_report.py --hook`

Requires Python 3.8+. No extra packages.

## Per-project settings (optional)
Put `.design-report.json` in each project folder:
```json
{"design_name": "Hotel Landing Page", "client_name": "Saffron Stays",
 "studio_name": "Your Studio", "currency": "INR", "fx_rate": 84, "markup_percent": 0}
```

## Three ways to get a report
1. **Automatic** – the SessionEnd hook writes `reports/ai-cost-*.html` every time you exit a session.
2. **Ask Claude** – "design is done, make the cost report" (uses the skill) or
   "use the design-cost-reporter agent".
3. **Manual** – `python3 ~/.claude/skills/design-cost-report/scripts/generate_report.py --all-sessions`

Prices: `skills/design-cost-report/scripts/pricing.json` (official rates as of 14 Oct 2026).
Update it if Anthropic changes prices.
