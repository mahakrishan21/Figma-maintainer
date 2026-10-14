---
description: Write the Slack update for the work done in this session, plus a separate internal token/cost block
argument-hint: [optional: which task or client]
---

Write the Slack update for the work done in this session ($ARGUMENTS if given, otherwise everything).

Use the agents' reports and Slack blocks from this conversation. One block per client or task, short and clear, with Slack formatting (*bold*, •), no node IDs or tool names:
```
*<Client> — <page / task>* (<date>)
Updated: <link>
• <what changed, 3–6 short bullets>
• <not done and why, if anything>
Questions for client:
• <images/video needed, missing fonts, missing content or links, decisions — or "None">
```
Then run `python3 -I ~/.claude/figma-maintainer/scripts/usage_report.py --slack` (add `--task "<words>"` for a single task) and show its output as a separate **Usage (internal)** block. Never put token or cost numbers in the client-facing block. If INR shows "set fx rate", mention it once.
