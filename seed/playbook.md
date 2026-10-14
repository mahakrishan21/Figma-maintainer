# Figma Maintainer Playbook

General rules for any client's file. One line each. Client-specific rules go in `clients/<client>.md`.

## Inspecting
- `get_metadata` on a whole page can come back empty or too large. Use a read-only `use_figma` script that lists `page.children` (id, name, x/y/w/h) and get the page from `node.parent` chains.
- Large `get_metadata` results get saved to a file. Pull out what you need with `jq`; don't read the whole thing.
- Frame names lie ("Updated", "Final", "Thank you" ×2). Tell versions apart by diffing text content and image hashes between the candidate and the original.
- A link to the originals doesn't mean edit them: check for later revision rounds first and build on the latest one (they may already hold part of the feedback).
- A quick version diff: gather `{kind, visible, characters | imageHash}` for every node in both frames and compare them as sets. That shows exactly what the designer changed.
- `node.screenshot()` across several nodes in one script may return only some images. Use `get_screenshot` for each node you need to see.

## Editing
- Scope = the frame or section in the link's node-id, never the page it sits on. Other frames on the same page are read-only. If there's no node-id, ask. (correction, 2026-10-14)
- A client's task configuration (`task-<name>.md`) applies only to that client. Reuse the task type, not another client's rules. (rule, 2026-10-14)
- Design desktop only unless the prompt explicitly asks for tablet/mobile frames; "should be responsive" isn't a request. Offer them at the end. (correction, 2026-10-14)
- Before setting `characters`, load every font the text currently uses (`getStyledTextSegments(['fontName'])`), including text inside instances.
- Change instance text as an override. Don't detach the instance.
- Reorder Auto Layout children with `parent.insertChild(index, node)`. Fields keep their component link.
- Put new top-level nodes below the bottom-most existing node (max of y+height) plus about 600px of spacing.
- Comment-matched node IDs point at the commented version. After duplicating, find the copies by text content; don't map by findAll index.
- Text with line separators: a regex literal containing U+2028 breaks the script (use `String.fromCharCode(0x2028)`), and deleting a paragraph can leave a leading `\n`. Check char codes after the edit.
- Annotations (`node.annotations = [{label}]`) work on instances. Use them for specs the canvas can't show, such as dropdown options and states.

## Images
- Image and video sources differ by client (iStock, Adobe Stock, AI, client-provided, existing assets). Always ask which one per slot before placing media; the client's preferred source is only the recommended option. (rule, 2026-10-13)

## Quality checks
- Image boxes often hide stacked image fills under the visible one (the last fill is on top). Report them; remove them only with approval. (rule, 2026-10-14)
- Never substitute a missing font (for example Libre Baskerville for Baskerville Display PT). Leave the text, and report the font and the layers. (correction, 2026-10-14)
- Dropdowns are drawn closed, so their option lists don't exist in the design. Annotate the options on the instance.
- Form rows: field heights, column gaps and label styles should match across rows. Dropdown variants are often 44px against 48px for text inputs. Compare `itemSpacing` of every row frame, including ones named "Frame 13xx".
- After a copy change, check whether the text now wraps to an extra line. Mention it if it changes the layout.
- When a workflow changes (for example "we'll call" becomes "we'll reach out"), search every placeholder, helper text and confirmation page for the old promise.
