---
disable-model-invocation: true
description: Token usage and API cost (USD + INR) — per task, this session, a client, or the full HTML report
argument-hint: [latest | session | "<task words>" | client <name> [since YYYY-MM-DD] | html [all-sessions]]
---

Use the usage-reporter agent (figma-maintainer:usage-reporter) for: $ARGUMENTS

If no argument is given, report this session (every task plus the main conversation). Show its "Usage (internal)" block as it is. Write the HTML report only when I said "html".
