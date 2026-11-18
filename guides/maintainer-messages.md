# Slack update and client message

> On-demand guide for the figma-maintainer agent. Read it when the task needs it; the core rules in the agent still apply.

## Slack update (always, at the very end)
After the report, add a section titled `Slack update (copy-paste)` holding one code block. Short and clear, under 12 lines, Slack formatting (*bold*, •), no markdown headings:
```
*<Client> — <page / task>* (<date>)
Updated: <link to the new or edited frame>
• <what changed, one short line each, 3–6 bullets>
• <what was not done, and why, if anything>
Questions for client:
• <images or video needed / which source; missing fonts; missing content or links; decisions — one line each, or "None">
```
Write it for the team and the client lead, not for designers: plain words, no node IDs, no tool names. Don't include token or cost numbers; the caller adds a separate "Usage (internal)" block from usage-reporter. The client-facing text goes in the Client message below.

## Client message (final comment, always, after the Slack update)
Add a section titled `Client message (copy-paste)` holding one plain-text code block: the final comment the team posts to the client (teaming comment, email or Figma). Write it for the **client**: friendly, plain English, correct grammar, no node IDs, tool names, internal notes, token or cost numbers.

Structure (keep this order; leave out a part only if it doesn't apply):
```
<Greeting, only if the client SOP sets one, e.g. "Hi Jesse," / "Dear Sir,">

<Opening: 1–2 sentences on what we've done, e.g. "We've updated the design according to your latest suggestions." / "The six inner pages are ready for your review.">

<Page name> - <one short note on what changed or what to look at>
<prototype link>

<Page name> - <note>
<prototype link>

Note: <placeholders still in the design, what we need from the client (images, copy, fonts, decisions), anything not done yet and why>

Thank you!
```
Rules:
- **Only claim what you verified.** Anything your report marks UNVERIFIED (for example hover or prototype playback) is not described as working. Write "please check the hover in the prototype" instead. The QA check compares every claim with Figma. (rule, 2026-10-29)
- **One block per page or frame** that changed, in page order, with the link right under its name.
- **Figma work = Figma PROTOTYPE link, never the design/page link.** For every frame you changed or created, build the link with `python3 -I ~/.claude/figma-maintainer/scripts/proto_link.py --file <fileKey> --node <id> [--node <id> …]`. It resolves the page and the screen frame (even from a nested node) and prints `https://www.figma.com/proto/<fileKey>/<File-Name>?page-id=…&node-id=…&starting-point-node-id=…&scaling=scale-down-width&content-scaling=fixed`. If the client or the task already gave a prototype link for that frame, reuse it. Use `figma.com/design/…` links only in the internal report and Slack update, never in the client message. (rule, 2026-10-23)
- **Work outside Figma** (an HTML preview, a document): use that preview link.
- The page note says what the client will see, in their words ("the Fredericksburg & Richmond images have been added to the locations"), not how it was done.
- **Note:** list every placeholder (sample copy, placeholder cards, watermarked stock photos) and what we need from them to replace it, plus open questions. Merge in the Slack update's "Questions for client". Leave the Note out if there's nothing to say.
- Keep it short: about 4–12 lines plus links. Fix grammar and typos; never invent changes that weren't made.
- Greeting and sign-off: use the client SOP's `Client message` settings (client.md §8) when set; otherwise no greeting and "Thank you!".

Reference examples (the team's format):
```
We've updated the design according to your latest suggestions.

Homepage - The Fredericksburg & Richmond images have been added to the locations, and the thumbnail perspective has been corrected for Decks, Fences and Patios (homepage only).
https://www.figma.com/proto/Bu1gCvMu3cNZIe3KqeuLxh/Veterans-Choice-Home?page-id=3%3A3&node-id=910-33

Thank you!
```
```
The six inner pages are ready for your review. Everything uses your Octopus copy word for word, except a few placeholders we added so you can see the layout:

About Wela
https://designervault-api.sitepreviews.dev/previews/.../about-wela.html

Note: We've used placeholder content in a few places so you can see the layout: a sample case study on the About page, placeholder advisor cards on the Managing Growing Complexity and Growing Your Business pages, and watermarked iStock photos throughout. We'll replace them once you approve the final images and provide the advisor photos for each page.

Thank you!
```
```
Dear Sir,

We have prepared an internal survey for the team to gather reflections on the usage of AI tools. Please find the responses at the link below:
<link>

Additionally, we have created a summary and presentation slides based on the above responses:
<link>

Kindly have a look and let us know if you have any specific analysis, thoughts or suggestions.
```

After a job that built or changed a page (not after audits or one-line fixes), end with: "Want a Consistency, Content or Accessibility Audit of this page?" Never run audits yourself; the auditor agents do them, read-only.
