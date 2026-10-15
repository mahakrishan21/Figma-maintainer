# Figma Maintainer Playbook

General rules for any client's file. One line each. Client-specific rules go in `clients/<client>.md`.

## Inspecting
- `get_metadata` on a whole page can come back empty or too large. Use a read-only `use_figma` script that lists `page.children` (id, name, x/y/w/h) and get the page from `node.parent` chains.
- Large `get_metadata` results get saved to a file. Pull out what you need with `jq`; don't read the whole thing.
- Frame names lie ("Updated", "Final", "Thank you" ×2). Tell versions apart by diffing text content and image hashes between the candidate and the original.
- A link to the originals doesn't mean edit them: check for later revision rounds first and build on the latest one (they may already hold part of the feedback).
- Check every task-supplied node ID with `getNodeByIdAsync` first; frames can be deleted between rounds. Report missing ones instead of rebuilding them unasked.
- A quick version diff: gather `{kind, visible, characters | imageHash}` for every node in both frames and compare them as sets. That shows exactly what the designer changed.
- `node.screenshot()` across several nodes in one script may return only some images. Use `get_screenshot` for each node you need to see.
- Tall full-page frames (~5000px) can time out in `get_screenshot`; screenshot section by section instead.

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

- `figma.saveVersionHistoryAsync` throws "not a supported API" in the use_figma runtime: no in-script checkpoint. Report it; duplicate first only if the change is substantial and approved. (2026-10-14)
- Text layers whose name equals their content auto-rename on a `characters` change ("Heading" became "Test passed"). Set `autoRename=false` first if the layer name must stay. (2026-10-14)
- The guard asks before any deletion. It reports "deletes N node(s)" for single deletes; loops over nodes with `.remove()` count as bulk deletes. Ancestor-walk scope checks are ignored. (rule, 2026-10-14)

## Images
- Image and video sources differ by client (iStock, Adobe Stock, AI, client-provided, existing assets). Always ask which one per slot before placing media; the client's preferred source is only the recommended option. (rule, 2026-10-13)

## Quality checks
- Image boxes often hide stacked image fills under the visible one (the last fill is on top). Report them; remove them only with approval. (rule, 2026-10-14)
- Never substitute a missing font (for example Libre Baskerville for Baskerville Display PT). Leave the text, and report the font and the layers. (correction, 2026-10-14)
- Dropdowns are drawn closed, so their option lists don't exist in the design. Annotate the options on the instance.
- Form rows: field heights, column gaps and label styles should match across rows. Dropdown variants are often 44px against 48px for text inputs. Compare `itemSpacing` of every row frame, including ones named "Frame 13xx".
- After a copy change, check whether the text now wraps to an extra line. Mention it if it changes the layout.
- When a workflow changes (for example "we'll call" becomes "we'll reach out"), search every placeholder, helper text and confirmation page for the old promise.

## Plugin API gotchas (2026-10-13)
- `figma.createAutoLayout()` frames get a default white fill. Set `fills=[]` on wrappers placed over coloured backgrounds.
- A child cloned from a horizontal row keeps `layoutSizingVertical='FILL'`. In a hugging vertical parent it collapses to ~1px, so set it to HUG after moving it. Switching a row to vertical needs `layoutSizingVertical='HUG'` too, or the second child gets clipped.
- Fonts missing from the plugin runtime (local-only families): text can be cloned, moved, `rescale()`d and `resize()`d, but its characters, fontSize and textAutoResize can't be changed. A resized text box doesn't reflow (height stays). Check `hasMissingFont` counts before any responsive job; if most text is affected, get a font decision first.
- Reaction actions take `resetScrollPosition`, not `preserveScrollPosition`. Use `SCROLL_ANIMATE` for SCROLL_TO.
- `getRangeFontName(0,1)` can return mixed on variable fonts. Read fonts from `getStyledTextSegments(['fontName'])`.
- Size and visibility counts from `findAll` change with `figma.skipInvisibleInstanceChildren`. Compare guard signatures inside the same run, or set the flag explicitly.
- Nested instances (a Logo inside a nav instance) can't be resized or rescaled. Build a breakpoint bar from fresh top-level instances instead.

## Responsive builds (2026-10-14)
- `node.clone()` of a frame inside a SECTION lands on the page, not the section: `section.appendChild(clone)` and set x/y relative to the section afterwards.
- When adapting by script, base every layout decision on the desktop widths/heights captured before any resize (FILL children shrink as soon as the parent does).
- Before resizing, pin absolute children with constraints: card/panel backgrounds STRETCH (or SCALE when margins are large), small icons MIN/MAX by their third. Otherwise backgrounds and icons are left behind or overflow.
- Run an overflow check (absoluteBoundingBox vs frame width, skipping clipped parents) on every new breakpoint frame before reporting.
- Sections copied from a boilerplate can carry their own explicit variable modes (e.g. Desktop). On responsive clones, clear them (`clearExplicitVariableModeForCollection`) or those sections ignore the page frame's mode. (2026-10-15)
- Switching a frame's layoutMode (H to V) can turn it or its children from FILL to HUG/FIXED width. Re-assert FILL afterwards and run a "narrower than parent" check. (2026-10-15)
- Assigning a value to a variable-bound property (itemSpacing, padding) silently unbinds it. Rebind with `setBoundVariable`, or unbind on purpose and report it. (2026-10-15)
- Position absolute overlays (cards, dropdowns, search panels) only after the final section sizing (FILL or bound width). If the parent resizes later, MAX/STRETCH constraints push them off-frame. (2026-10-15)
