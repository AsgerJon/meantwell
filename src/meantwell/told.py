"""
The 'told' module sorts the parts an instruction is told with by their
kinds (SPEC.md 21.19 S1), for the short words: Verb.OPEN(chest),
Question.IDENTIFY(stone). A part is a thing by its mcdex member, a place
(a BlockPos or a Vec3), a whole number, or a thing with its own place:
anything with a 'member' and a 'pos', as a scene's Thing has in unitTAS.
Such a thing is only ever asked those two: never its truth, which in
unitTAS is an examination by command.

- handle(part): the (member, place) of a thing with its own place, or
  None for anything else.
- parts(what, given): the (thing, place, number) told, None for each
  not told.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any, Optional

from mcdex import MCThing

from unittas.values import BlockPos, Vec3


def handle(part: Any) -> Optional[tuple]:
  """The (member, place) of a thing with its own place; None for a
  part that isn't one."""
  if isinstance(part, (MCThing, BlockPos, Vec3)):
    return None
  if not (hasattr(part, 'member') and hasattr(part, 'pos')):
    return None
  return part.member, part.pos


def parts(what: str, given: tuple) -> tuple:
  """
  The parts 'what' (an action to use, say) is told with, by their
  kinds: (thing, place, number), None for each not told.

  Raises
  ------
  TypeError
    Two things, two places or two numbers; or a part of another kind,
    named.
  """
  told = {}
  for part in given:
    both = handle(part)
    if both is not None:
      found = (('thing', both[0]), ('place', both[1]))
    elif isinstance(part, MCThing):
      found = (('thing', part),)
    elif isinstance(part, (BlockPos, Vec3)):
      found = (('place', part),)
    elif isinstance(part, int) and not isinstance(part, bool):
      found = (('number', part),)
    else:
      infoSpec = """%s is told by an mcdex member, a place (a BlockPos or
      a Vec3), a thing with its own place, or a whole number, not %r"""
      raise TypeError(' '.join((infoSpec % (what, part)).split()))
    for kind, value in found:
      if kind in told:
        infoSpec = """%s is told two %ss: %r and %r"""
        raise TypeError(infoSpec % (what, kind, told[kind], value))
      told[kind] = value
  return told.get('thing'), told.get('place'), told.get('number')
