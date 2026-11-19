"""
The 'meantwell' package is a robotic Minecraft player that tries to help
you and follow your instructions (SPEC.md 21): a player and nothing more
(unitTAS's SPEC.md 15.2), given abstract steps by a test, a person or a
program. Its body is unitTAS's: the game, the probe's protocol and,
until the lift-out (SPEC.md 21.7 step 8), the agent's skills.

Being built: instructions and what follows them (SPEC.md 21.7 step 3),
and maneuvering (SPEC.md 21.11).

- instruction, action, examination, steps, when: what the helper can be
  told, each a value; verb and question, their closed sets, each member
  called with its parts the short word for its value; told, how the
  parts are told apart.
- outcome: what came of an instruction, done or not, and the line said.
- helper: Helper, an agent and someone to tell, which follows them, or
  must do them.
- helpertestcase: HelperTestCase, the front for unitTAS's tests, and
  the one module here that takes anything of unitTAS's testing.
- words: how things are said.
- atlas: Atlas, what the agent remembers of the ground, look by look.
- traveller: Traveller, long trips on what it remembers.
- routine: Routine, what the routines below share: a body played
  directly by a player's means, and the keys it holds.
- swimmer: Swimmer, to a place as 1.13 swims, or upright at the top.
- glide: how an elytra flies and comes down, as the game reckons it.
- glider: Glider, which opens its wings and glides to a place.
- castdoes, castmove, portalcast: the plan of a nether portal cast
  beside a lake of lava with one bucket, each move a value.
- portalcaster: PortalCaster, which plays that plan move by move.
- mouse: Mouse, a body whose look is turned as a hand turns a mouse.
- pace: how a player walks on the ground, as the game reckons it.
- walker: Walker, which walks a way as a player does, turned by the
  mouse.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

__version__ = '0.1.0.dev0'
