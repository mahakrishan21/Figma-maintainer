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
- Before setting `characters`, load every font the text currently uses (`getStyledTextSegments(['fontName'])`), including text inside instances.
- Change instance text as an override. Don't detach the instance.
- Reorder Auto Layout children with `parent.insertChild(index, node)`. Fields keep their component link.
- Put new top-level nodes below the bottom-most existing node (max of y+height) plus about 600px of spacing.
- Annotations (`node.annotations = [{label}]`) work on instances. Use them for specs the canvas can't show, such as dropdown options and states.

## Images
- Stock images are watermarked iStock comps (Basic plan/Essentials, Editorial first) used as approval placeholders. Fetch them with `scripts/istock_fetch.py`, name the layer `iStock <id> – placeholder`, log the IDs to buy, and swap in the purchased files after approval. (rule, 2026-10-12)

## Quality checks
- Image boxes often hide stacked image fills under the visible one (the last fill is on top). Keep one fill per box.
- Dropdowns are drawn closed, so their option lists don't exist in the design. Annotate the options on the instance.
- Form rows: field heights, column gaps and label styles should match across rows. Dropdown variants are often 44px against 48px for text inputs. Compare `itemSpacing` of every row frame, including ones named "Frame 13xx".
- After a copy change, check whether the text now wraps to an extra line. Mention it if it changes the layout.
- When a workflow changes (for example "we'll call" becomes "we'll reach out"), search every placeholder, helper text and confirmation page for the old promise.
