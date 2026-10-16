---
disable-model-invocation: true
name: components-and-interactions
description: How to understand and safely change Figma components and their behaviour — component sets and variants, component properties (variant, boolean, text, instance swap, slot), nested instances and overrides, interactive components (hover, pressed, focus, open/closed states driven by prototype reactions), prototype flows and overlays, Smart Animate, and variables/modes. Use whenever a change touches a hover/pressed/active/disabled state, a variant, a component property, a dropdown/accordion/tab/menu behaviour, a prototype interaction, or anything reached through a main component rather than a plain frame, or when running /figma-maintainer:components-and-interactions.
---

# Components, states and interactions

Plain frame edits change one thing. Component edits change every instance of the component, in every file that uses the library. Understand the structure before you touch it, and work out how far the change will spread before you make it.

## 1. Classify the change first
Work out which layer the request actually lives on:

| Request sounds like | It really is | Where to change it |
|---|---|---|
| "Button hover should be darker" | A variant (`State=Hover`) of a component set | The **Hover variant** inside the main component set |
| "Make hover work in the prototype" | **Interactive component**: a reaction on the Default variant (`While hovering` / `Mouse enter` → **Change to** Hover) | Reactions on the variant(s) in the set |
| "This one card should show the icon" | A **boolean/instance-swap property** on one instance | Instance override, not the main component |
| "All cards should have 24px padding" | Main component structure | Main component, after the spread check |
| "Dropdown should open on click" | Interactive component (`On click` → Change to `Open`) or an **overlay** | Variant reactions, or a prototype overlay on the trigger |
| "Use the dark version here" | **Variable mode** (`explicitVariableModes`) or a variant (`Theme=Dark`) | The frame's mode, or a variant swap on the instance |
| "Tab 2 should go to the pricing page" | A prototype **navigation** reaction | Reactions on the instance or frame |
| "Text in the button" | A **text property** or an instance text override | `instance.setProperties` or a text override, never a detach |

If the request is ambiguous between "this instance" and "the component everywhere", that's a decision for the user. Ask, giving the spread numbers from section 3.

## 2. Inspect the structure (read-only, before editing)
Run one read-only `use_figma` script on the target and collect:
- **Node chain:** for an instance, `getMainComponentAsync()` → main component → `parent` (a COMPONENT_SET when it has variants), and `mainComponent.remote` (true means a library component: you can't edit it in this file).
- **Component set:** `componentPropertyDefinitions` (each property's type, default and variant options), the list of variants and their `name` ("State=Hover, Size=md"), and any variants missing from the full grid (for example, there's no `Disabled` for `Size=sm`).
- **Instance:** `componentProperties` (current values), `overrides` (which fields are overridden on the instance), and nested instances with `exposedInstances`.
- **Reactions** on each variant and on the instance: `node.reactions` → trigger type (`ON_HOVER`, `WHILE_HOVERING`, `MOUSE_ENTER`, `MOUSE_LEAVE`, `ON_CLICK`, `ON_PRESS`, `WHILE_PRESSING`, `AFTER_TIMEOUT`, `ON_KEY_DOWN`), plus the actions (`navigation`: `CHANGE_TO` / `NAVIGATE` / `OVERLAY` / `SWAP` / `SCROLL_TO` / `BACK` / `CLOSE`, `destinationId`, and the transition with its easing and duration).
- **Variables:** `boundVariables` on fills, strokes, spacing, radius and text, the collection and mode, and the frame's `explicitVariableModes`.
- **Styles:** `fillStyleId`, `textStyleId` and `effectStyleId` on the layers you'll change.

Summarise this for yourself as a short state map before you edit, for example: `Button set: State {Default, Hover, Pressed, Disabled} × Size {sm, md}; Default --WHILE_HOVERING→CHANGE_TO→ Hover (Smart Animate 150ms ease-out); Hover fill = var color/primary/600`.

## 3. Check how far the change spreads (always, before changing a main component)
- Count the instances of the main component, or of every variant in the set: `figma.root.findAllWithCriteria({types:['INSTANCE']})` filtered by `mainComponent.id` (or by the component set's `key`). Group them by page and top-level frame.
- If the component is **remote** (from a library), you can't edit it here. Report that the change belongs in the library file, or ask whether to override it on the instances in scope instead.
- **The rule:** edit the main component or component set without asking only when the task clearly means "the component everywhere", or when every instance is inside the frames the task covers. Otherwise, stop and ask: "Change the component (affects N instances on pages A, B) or only these instances (overrides)?"
- Never detach an instance to make a state change work. If a fix only works with a detach, report it instead.

## 4. Making the change
- **Style of a state (hover colour, border, shadow):** edit that variant only. Bind to the existing variable or style (for example `color/primary/600`), never a raw hex when a token exists. Keep every other property identical to the Default variant, unless the state is meant to change it.
- **Add a missing state:** duplicate the closest variant inside the set, rename it with exact property syntax (`State=Hover, Size=md`), adjust it, and keep the variant grid complete. If one size gets Hover, every size gets Hover.
- **Make a state interactive:** on the source variant, call `await node.setReactionsAsync([...])` with a `CHANGE_TO` action to the target variant's id.
  - **Hover:** `WHILE_HOVERING` on Default → Hover (it reverts on its own); or `MOUSE_ENTER` → Hover plus `MOUSE_LEAVE` on Hover → Default.
  - **Pressed:** `WHILE_PRESSING` → Pressed.
  - **Click toggles** (dropdown, accordion, checkbox): `ON_CLICK` Closed → Open, and `ON_CLICK` Open → Closed.
  - **Transition:** match what the file already uses (usually `SMART_ANIMATE`, 150–300ms, `EASE_OUT`). If the file has no precedent, use Smart Animate, 200ms, ease-out, and say so.
  - **Keep existing reactions:** read the current reactions and append or replace only the one you're changing.
- **Component properties:** add them with `addComponentProperty(name, type, default)` and link layers with `componentPropertyReferences` (`visible` for boolean, `characters` for text, `mainComponent` for instance swap). Rename them with `editComponentProperty`, which keeps instance values. Never delete a property that instances use without reporting it.
- **On instances:** change variants or properties with `instance.setProperties({State:'Hover', 'Show icon#123:0': true})`. Use the exact property keys from `componentProperties`, including the `#id` suffix on non-variant properties.
- **Nested instances:** change them through the parent's exposed property where one exists. Otherwise swap the nested instance (`swapComponent`) inside the main component, after the spread check.
- **Prototype flows and overlays:** `NAVIGATE` needs a destination top-level frame. `OVERLAY` needs an overlay frame and `overlayRelativePosition` / `overlayPositionType`. Check that the destination exists and sits on the same page.
- **Variables and modes:** change a mode per frame with `setExplicitVariableModeForCollection(collection, modeId)`. Never edit a variable's value unless the task explicitly means "the token everywhere"; that changes every bound layer in the file and its consumers.

## 5. Verify
- Read back the variant names, property definitions and reactions after the change, and compare them with your state map. Report the before → after.
- Take a screenshot of each changed variant next to its Default variant so the state difference is visible.
- Instance check: pick 2–3 instances in scope and confirm they picked up the change, and that overridden instances kept their overrides.
- Make sure no instance was detached, and no unrelated variant changed (compare the other variants' fills, text and size before and after).
- Prototype: `reactions` resolve to existing nodes (no dangling `destinationId`), and the flow's starting point still exists. Note that the user should click through it in Present mode; you can't play the prototype yourself.

## 6. Report
- The state map before → after, in one line per variant or reaction.
- How far the change spread: N instances on pages X and Y, and whether you changed the main component or used overrides.
- Anything you couldn't do here (a remote library component, needing a detach, an unclear scope).
- What the user should click through in Present mode to confirm.
