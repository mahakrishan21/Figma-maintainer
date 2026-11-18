# QA fix round

> On-demand guide for the figma-maintainer agent. Read it when the task needs it; the core rules in the agent still apply.

Use this when the task says "QA fix round" and lists items from `qa.md` (the qa-checker's report).

- Work in the **same job folder** and the **same output frames** QA names. Don't duplicate again, don't create new frames, and don't touch anything else.
- Fix **only the listed AUTO-FIX items**, each to the expected value QA gives. If an item turns out to need a decision, don't do it; return it as a question.
- Take a fresh before snapshot of the page first, and run the usual after-snapshot compare with `--targets` set to the output frames.
- Update `comments-applied.md`, the report, the Slack update and the client message so they match the fixed state. Add a line "QA fix round <n>: <items fixed>" to the report.
