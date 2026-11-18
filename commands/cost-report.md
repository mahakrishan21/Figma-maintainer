---
disable-model-invocation: true
description: Token usage and API cost (USD + INR) for this conversation or one task
argument-hint: [latest | "<task words>" | html]
---

Use the usage-reporter agent (figma-maintainer:usage-reporter) for: $ARGUMENTS

This report covers **one conversation or one task only**:
- **no argument:** this conversation (every plugin task plus the main conversation);
- **`latest`:** the task that just finished;
- **`"<task words>"`:** the one task whose description matches;
- **`html`:** an HTML report of this conversation only.

Show its "Usage (internal)" block as it is.

If I ask here for a client, a period or all jobs, don't run anything. Answer: "This report covers one conversation or one task. For everything on this Mac, run `/figma-maintainer:cost-report-all`."
