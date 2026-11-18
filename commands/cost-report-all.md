---
disable-model-invocation: true
description: Consolidated cost history of everything done with figma-maintainer on this Mac (sessions, clients, agents); only when asked
argument-hint: [since YYYY-MM-DD] [client <name>] [html]
---

Use the usage-reporter agent (figma-maintainer:usage-reporter) with this brief:
```
Consolidated: python3 -I ~/.claude/figma-maintainer/scripts/usage_report.py --all [--since <date>] [--client "<name>"] [--html]
```
Fill in the options from my note ($ARGUMENTS): `since YYYY-MM-DD` → `--since`, `client <name>` → `--client`, `html` → `--html`.

The report covers this Mac only:
- the total, split into main conversations and plugin tasks;
- one line per session;
- totals per client;
- averages per agent, with the cost split by model.

Show it as it is, inside a code block titled **Usage history (internal)**. If it wrote an HTML file, give the path. This report is never added to Slack updates or client messages.
