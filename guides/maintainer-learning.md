# Learning: records, PROJECT.md and SOP updates

> On-demand guide for the figma-maintainer agent. Read it when the task needs it; the core rules in the agent still apply.

**SOPs live only in the plugin**, the single source of truth. One SOP manager maintains them. The links in `~/.claude/figma-maintainer/` (`clients/`, `playbook.md`, `pricing.json`, `cost-config.json`) point into the plugin's `knowledge/` folder. Everything else in that folder is this person's **session files**: `job-log.md`, logs, `audits/`, `reports/` and `contributions/`.

At the end of every task:
- **Always, in the job folder** (`jobs/<date>-<task>/`), save:
  - `report.md`: the full completion report;
  - `slack.md`;
  - `client-message.md`;
  - in comments mode, `comments-applied.md`: each comment's date, author and text, with done / not done / skipped-older status and the node changed.
- **Always, rewrite `PROJECT.md`** so it reflects the project **now**:
  - latest frames with prototype links, and current status;
  - new client decisions (dated);
  - open items (add new ones, remove resolved ones);
  - the comment round you applied, and one job-history line pointing to the job folder.

  Rewrite sections rather than piling up text; the job folders keep the history.
- **Always:** append one entry (max ~6 lines) to the **project's** `job-log.md` in the project folder: date, task, file/node, what changed, open items, and any correction received. Also add **one index line** to `~/.claude/figma-maintainer/job-log.md`: `<date> · <agency> › <project> · <task> · <project folder>`. Save the Slack update text in `slack/<YYYY-MM-DD>-<task>.md`.
- **SOP manager's machine** (`~/.claude/figma-maintainer/.master` exists):
  - Put new or corrected rules straight into the right SOP section: project facts in the project file, client-wide rules in `client.md`, recurring-task rules in the client's `task-*.md`, and cross-client lessons in `playbook.md` (one line, no duplicates).
  - Tag every rule with its source and date. Corrections are tagged `(correction, YYYY-MM-DD)`.
  - Remind the user to commit and run `/figma-maintainer:share`.
- **Co-worker's machine** (no `.master`): **never edit SOPs.** The SOP guard blocks it.
  - For each new client requirement, correction or workflow improvement, write a proposal file `~/.claude/figma-maintainer/contributions/<YYYY-MM-DD>-<agency>-<topic>.md`, using the format in `clients/_template/contribution.md`.
  - List the proposals in the report, and tell the user to send them with `/figma-maintainer:contribute`.
- When the user's message contains a correction ("no, always…", "next time…", "that's wrong"), apply it to the current job now, then record it as above.
- Keep SOPs tight. On the SOP manager's machine, merge or delete rules that turn out to be wrong or redundant.

## SOP format and rules
- **SOP format:** `client.md` has 10 numbered sections (overview, contacts, workflow and versioning, design standards, content, images and video, forms, handoff, hard rules, rule log), and each project file has 9. A `<not set>` field means unknown: ask, or use the team default the template names. When a rule is stated, write it into its section with source and date, and add a rule-log line.
- **Never invent SOP rules.** The SOPs are built over time from what the user or client actually says. Record a rule only when they state it, with its date and source (for example "(rule from the user, 2026-10-14)"). Leave placeholders as they are. SOPs are edited only on the SOP manager's machine; co-workers write contributions (see Learning).
