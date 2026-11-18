"""
The 'meantwell' package is a robotic Minecraft player that tries to help
you and follow your instructions (SPEC.md 21): a player and nothing more
(unitTAS's SPEC.md 15.2), given abstract steps by a test, a person or a
program. Its body is unitTAS's: the game, the probe's protocol and,
until the lift-out (SPEC.md 21.7 step 8), the agent's skills.

Being built: instructions and what follows them (SPEC.md 21.7 step 3).

- instruction, action, examination, steps, when: what the helper can be
  told, each a value; verb and question, their closed sets.
- outcome: what came of an instruction, done or not, and the line said.
- helper: Helper, an agent and someone to tell, which follows them.
- words: how things are said.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

__version__ = '0.1.0.dev0'
