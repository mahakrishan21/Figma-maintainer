# Figma Maintainer Playbook

General rules for any client's file. One line each. Client-specific rules go in `clients/<client>.md`.

## Inspecting
- `get_metadata` on a whole page can come back empty or too large. Use a read-only `use_figma` script that lists `page.children` (id, name, x/y/w/h) and get the page from `node.parent` chains.
- Large `get_metadata` results get saved to a file. Pull out what you need with `jq`; don't read the whole thing.
- Frame names lie ("Updated", "Final", "Thank you" ×2). Tell versions apart by diffing text content and image hashes between the candidate and the original.
- A link to the originals doesn't mean edit them: check for later revision rounds first and build on the latest one (they may already hold part of the feedback).
- Check every task-supplied node ID with `getNodeByIdAsync` first; frames can be deleted between rounds. Report missing ones instead of rebuilding them unasked.
- A frame the user calls a duplicate can be an empty frame of the same size. Count its descendants (Plugin API and REST snapshot) before mapping ids; if it's empty, stop and ask whether to fill it from the source. (2026-11-04)
- A quick version diff: gather `{kind, visible, characters | imageHash}` for every node in both frames and compare them as sets. That shows exactly what the designer changed.
- "Not edited since version X?": compare REST `GET /files/<key>/nodes?ids=<id>` with the same call plus `&version=<X>`, node by node with figma_snapshot's `node_sig`. 0 diffs and an unchanged file `version` mean untouched. (2026-10-29)
- `node.screenshot()` across several nodes in one script may return only some images. Use `get_screenshot` for each node you need to see.
- Tall full-page frames (~5000px) can time out in `get_screenshot`; screenshot section by section instead.

## Editing
- Client feedback and revisions (default, every client): always duplicate the current design frame first and make the changes only in the duplicate. The previous version stays untouched as the backup. Don't ask and don't look for a client SOP first; this is the standard behaviour. (correction from the user, 2026-10-29)
- Name the new frame with the version and the date, e.g. "Homepage V2 - 29 Oct 2026"; the next round is "Homepage V3 - <date>". (correction from the user, 2026-10-29)
- "Looks like you don't have edit access to this file" from `create_session`/`get_metadata`/`use_figma` means the Figma MCP account (check `whoami`) isn't an editor, even if the REST token can read. Stop, do read-only prep via REST, and ask the file owner to share edit access with that account. (2026-10-23)
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
- In a fresh `frame.clone()`, find copied nodes by the source's child-index path, and instance sublayers as `'I' + copiedInstanceId + ';' + <original sublayer suffix>`. This avoids `getMainComponentAsync`, which the guard flags near writes. Annotations also work on instance sublayers. (2026-10-27)

- Wireframes can carry a locked full-page "Overlay" (white fill, COLOR blend) that greys out everything under it. When a revision changes the page height, resize it with the frame, or the new area shows in colour. (2026-10-29)
- Page frames without Auto Layout (sections stacked by y): after a section height change, resize the frame first (resize applies child constraints), then re-set each section's y from the original's gaps, keeping its 1px overlaps. (2026-10-29)
- Growing a frame whose children have SCALE or CENTER constraints (video poster with a play button and overlay): use `resizeWithoutConstraints`, then move or resize by hand only the children that must follow. (2026-11-17)
- `resize()` on a layer with a CROP image fill keeps `imageTransform`, so the photo stretches. Recompute the crop from the image's pixel size (`figma.getImageByHash(hash).getSizeAsync()`) so the visible region has the box's aspect ratio, keeping the crop centre. (2026-11-17)

- `figma.saveVersionHistoryAsync` throws "not a supported API" in the use_figma runtime: no in-script checkpoint. Report it; duplicate first only if the change is substantial and approved. (2026-10-14)
- Text layers whose name equals their content auto-rename on a `characters` change ("Heading" became "Test passed"). Set `autoRename=false` first if the layer name must stay. (2026-10-14)
- No tool duplicates a whole Figma file: `create_new_file` makes a blank file, REST has no copy endpoint, and `use_figma` can't move nodes between files. For "work in a copy", stop before editing. Ask the user to duplicate the file in Figma, give the MCP account (`whoami`) edit access, and send the new link. (2026-10-27)
- Before a comment or copy round, check that every font in the target text loads (`loadFontAsync`). If one doesn't, stop before editing text and tell the user the font name, styles and layers, so they can install or activate it; then re-check and continue with the real font. Annotate the new copy for a designer to type in the desktop app only when the user chooses that. (correction from the user, 2026-10-29; replaces the 27 Oct annotate-first workaround)
- `upload_assets` with `nodeIds` replaces the whole fills array. On stacked fills (photo + gradients + cutout), rebuild the stack afterwards with only the photo hash swapped. In a same-file copy, read the stack from the untouched source node. `figma_snapshot` doesn't cover annotations, so verify them by read-back. (2026-10-27)
- The guard asks before any deletion. It reports "deletes N node(s)" for single deletes; loops over nodes with `.remove()` count as bulk deletes. Ancestor-walk scope checks are ignored. (rule, 2026-10-14)

## Images
- Image and video sources differ by client (iStock, Adobe Stock, AI, client-provided, existing assets). Always ask which one per slot before placing media; the client's preferred source is only the recommended option. (rule, 2026-10-13)

- `upload_assets` `nodeIds` only takes plain IDs (no instance sublayers `I…;…`). For card images inside instances, upload onto a plain in-scope frame with no fills, copy the imageHash to the sublayer, then reset that frame's fills. On stacked fills (image under gradients), rebuild the fills array from the original with only the imageHash swapped. (2026-10-23)

- `fetch_assets.py` skips `.jfif` Drive files without listing them as failed, so compare the saved count with the number of links. Fetch a `.jfif` by hand (it's a JPEG) and save it as `.jpg`. (2026-10-27)

## Quality checks
- Image boxes often hide stacked image fills under the visible one (the last fill is on top). Report them; remove them only with approval. (rule, 2026-10-14)
- A REST font list can name fonts nobody sees: a text layer's `style` is its base style, and when `characterStyleOverrides` covers every character the base font (often a leftover from an earlier stage) renders nowhere. Count characters per font, or use `getStyledTextSegments`, before calling it a font mismatch. To clear it with no visible change: set the node's `fontName`, re-apply each range's font, and assert the segments are identical. (2026-11-12)
- Never substitute a missing font (for example Libre Baskerville for Baskerville Display PT). Leave the text, and report the font and the layers. (correction, 2026-10-14)
- The snapshot compare can flag button instances in the untouched source frame after a clone: Figma re-measures instance labels that were stored with fallback-font metrics once the real font is loaded (REST `lineHeightPx` 21.09 → 26.46, button 62 → 66px tall). Diff those nodes over REST against the before version (`&version=<id>`) to confirm it's size only, report it, and never edit the original to "fix" it. Likely trigger: walking the source's instance sublayers (`findAll` with `skipInvisibleInstanceChildren=false`), so count layers on protected frames another way. (2026-11-17, cause not proven)
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
- Size and visibility counts from `findAll` change with `figma.skipInvisibleInstanceChildren`. Compare guard signatures inside the same run, or set the flag explicitly. Even in one run a fresh section clone counted 4191 nodes against the source's 4347 until the flag was set to false; then compare per frame as multisets. (2026-10-29)
- Annotation `label` reads back HTML-escaped (`&amp;`, `&#39;`, `&quot;`) even when written plain. Unescape before comparing; check long labels by checksum. (2026-10-29)
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

## Copy docs and scripts (2026-10-23)
- Google Docs with pending suggestions: `read_file_content` merges insertions and deletions into one string ("equipment system"). Export the doc as .docx (`download_file_content`) and read `w:ins`/`w:del`. Decode the base64 from the session transcript; don't retype it. (2026-10-23)
- A `use_figma` call that fails with a transport error ("Invalid content from server", "connection lost") may or may not have run: read the canvas before retrying, and start write scripts with an "already changed?" check so a retry can't apply twice. (2026-11-04)
- A `use_figma` script that throws is rolled back as a whole: a clone made before the error didn't persist. Still re-read the canvas before retrying. (2026-10-23)
- Exact text matches can fail on a leading non-breaking space (U+00A0, e.g. " Call to Discuss"). Match with `String.fromCharCode(160)` or normalize first. (2026-10-23)
- upload_assets: POST each URL with `curl -sS` and check the JSON (`success`, `imageHash`). Backgrounded parallel curls in one shell call failed silently. (2026-10-23)
- A hug-width text cloned into a FILL slot shows its hidden `textAlignHorizontal` (the footer field label was CENTER), so set LEFT explicitly. (2026-10-23)
- Google Docs tabs: a `tab=t.…` link can point to content the connector doesn't separate. Fetch the tab with `…/export?format=docx&tab=<tabId>` (or `format=txt`). The txt export drops pending suggestions (pre-suggestion text) while the docx keeps them with author and date, so compare both before calling copy "different". (correction, 2026-10-23)
- Hidden-layer overrides on an instance survive variant switches when the layers have the same name in every variant; check by cycling `setProperties` through the variants on the copy and restoring the start value. (2026-11-12)
- Same-job revision rounds: compare the page with the last after snapshot before editing. A hand edit made in between (e.g. a button moved) changes heights the earlier records quote; leave it as found, report it, and re-measure. (2026-11-12)
- FILL-width cards in a row can come out unequal by a pixel or two; in a fixed container set equal fixed widths, and set `strokesIncludedInLayout=false` so bordered and borderless cards share the same inner padding. (2026-11-12)
