# What's new in figma-maintainer

Newest first. `/figma-maintainer:about` shows the latest three versions.

## 1.38.0 · 25 Nov 2026
- New `/figma-maintainer:check-figma`: shows the connected Figma account (name and email) and asks you to confirm it. It runs by itself before the first Figma job in each conversation, and Figma edits wait until you confirm, so work never runs under the wrong account on a shared setup.

## 1.37.0 · 25 Nov 2026
- Lower token use on every job: agents no longer carry unused tool definitions (about 25k fewer tokens on every step).
- The client SOP, playbook and project history load as one short digest instead of many file reads.
- QA prints a short summary and puts all before/after crops on one contact sheet; agents ask job files short questions instead of reading them whole.
- A hook asks you before an agent looks at more images than its budget.

## 1.36.0 · 25 Nov 2026
- New `/figma-maintainer:about`: version, release date, what the plugin can do, what's new, and an update check.
- Asks once per session to update when a newer version is live in the team repo.
- Removed the `sop`, `contribute`, `share` and `review-contributions` commands. Add SOP rules with a plain prompt (`figma-maintainer: Lasso Up desktop frames are 1920`).

## 1.35.0 · 25 Nov 2026
- New `/figma-maintainer:make-inner-page`: designs an inner page from the homepage in its exact style (header, footer, grid, type, colours, components), next to the homepage.

## 1.34.0 · 19 Nov 2026
- iStock works on every team Mac and checks itself; when it can't connect, it says why and how to fix it.
- GitHub sign-in steps (`gh auth login`) for installing from the team repo.

## 1.33.5 · 19 Nov 2026
- The team marketplace moved to the E2M-Design organization.

## 1.33.3 · 18 Nov 2026
- Install and update from the private team marketplace (`e2m-figma`).

## 1.33.0 · 18 Nov 2026
- Lower token use and cost; cost reports per conversation or task.

## 1.32.0 · 2 Nov 2026
- Ready for the team: onboarding, the visual guide, the missing-font rule, one team Figma token.

## 1.30.0 · 29 Oct 2026
- `/figma-maintainer:qa` runs the QA check on its own, including on manual work.

## 1.29.0 · 29 Oct 2026
- Independent QA check after every figma-maintainer job.

## 1.28.0 · 27 Oct 2026
- Client comments found automatically, planned, approved, then applied.
