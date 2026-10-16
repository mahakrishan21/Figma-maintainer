---
disable-model-invocation: true
description: List the Figma comments on a frame (read-only), each matched to the layer it points at
argument-hint: <figma URL with node-id> [--all-frames] [--author "Name"]
---

Run `python3 -I ~/.claude/figma-maintainer/scripts/figma_comments.py --url <url> --out <project folder>/comments`, passing any extra flags from: $ARGUMENTS

Present the comments grouped by frame, top to bottom. Show what each one points at (the matched text or image), and sort them into copy/layout changes, image editing, approvals and questions. Don't change anything in Figma. If the script reports no Figma token, explain how to set `FIGMA_TOKEN` (Figma → Settings → Security → Personal access tokens, read access to File content and Comments) and never ask for the token in chat.

Store every file this produces in the project folder from `python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>"` (person › agency › project; created only if missing).
