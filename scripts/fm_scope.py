"""Is this figma-maintainer work? Shared by the plugin's hooks so they stay silent in every other session
(website builds, other plugins, general chat).

Active ONLY when:
  - the prompt names the plugin ("figma-maintainer", "figma maintainer", "/figma-maintainer:..."), or
  - this session has already run a figma-maintainer agent or command (follow-ups), or
  - the call comes from a figma-maintainer agent.
Being installed is not enough. A Figma link or an "audit" request on its own is NOT enough: other plugins
(e.g. the website generator's Figma import) use them too.
"""
import re
from pathlib import Path

EXPLICIT = re.compile(r"figma[\s_-]*maintainer|/figma-maintainer:", re.I)
# Traces only real use leaves in the transcript (agent launches, slash commands, this plugin's hook output).
# No plain-text phrases: a README or pasted doc that mentions the plugin must not switch it on.
SESSION_MARKERS = ('"subagent_type":"figma-maintainer:', '"subagent_type": "figma-maintainer:',
                   '<command-name>/figma-maintainer:', 'figma-maintainer image gate:')


def session_used_plugin(transcript_path):
    try:
        p = Path(transcript_path)
        if not p.is_file():
            return False
        size = p.stat().st_size
        with open(p, "rb") as f:
            if size > 20_000_000:  # very long sessions: check the most recent part only
                f.seek(size - 20_000_000)
            data = f.read().decode("utf-8", "ignore")
        return any(m in data for m in SESSION_MARKERS)
    except Exception:
        return False


def is_fm_agent(agent_type):
    return (agent_type or "").startswith("figma-maintainer:")


def prompt_is_fm(prompt, transcript_path):
    if EXPLICIT.search(prompt or ""):
        return True
    return session_used_plugin(transcript_path)
