"""
Action: something the agent is told to do (SPEC.md 21.7 step 3): a verb,
with the thing and the place its verb needs and no others. The agent
infers the rest, as a player (unitTAS's SPEC.md 15.2): the way there,
the look, the click.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from mcdex import MCThing
from worktoy.ezdata import EZField

from unittas.values import BlockPos, Vec3

from .instruction import Instruction
from .verb import Verb
from .words import named, where

#  Whether a verb's action names a part: it must, it may, or it can't
_MUST, _MAY, _CANT = 'must', 'may', 'cant'
#  What each verb's action names: its thing, its place, and whether it
#  takes a tick budget (a wait's ticks are how long it waits)
_NAMES = {
  Verb.GO: (_CANT, _MUST, True),
  Verb.USE: (_MAY, _MUST, True),
  Verb.BREAK: (_MAY, _MUST, True),
  Verb.OPEN: (_MAY, _MUST, True),
  Verb.PLACE: (_MUST, _MUST, True),
  Verb.TAKE: (_MUST, _CANT, False),
  Verb.PUT: (_MUST, _CANT, False),
  Verb.CLOSE: (_CANT, _CANT, False),
  Verb.WAIT: (_CANT, _CANT, True),
}


class Action(Instruction, frozen=True):
  """
  An action: its 'verb'; its 'thing', an mcdex member (the item to take,
  put or place; for a block used, broken or opened, what is said to be
  there), or None; its 'place' (a BlockPos; to go, a Vec3 too), or None;
  and its 'ticks', the step's tick budget (0: the agent's own), or how
  long a wait is. Made with a part its verb lacks or can't have, it is
  refused at once.

    Action(Verb.USE, MCBlocks.Lever, BlockPos(5, 4, 7))
    Action(Verb.TAKE, MCItems.PinkWool)
    Action(Verb.GO, place=Vec3(6.5, 4.0, 4.5), ticks=200)
    Action(Verb.WAIT, ticks=40)

  Raises
  ------
  TypeError
    A part its verb needs is missing, one it can't have is given, or one
    is of the wrong kind.
  ValueError
    Ticks below 0, or a wait of none.
  """

  verb = EZField[Verb](Verb.WAIT)
  thing = EZField[object](None)
  place = EZField[object](None)
  ticks = EZField[int](0)

  def __post_init__(self) -> None:
    thing, place, budget = _NAMES[self.verb]
    self._checkThing(thing)
    self._checkPlace(place)
    if not budget and self.ticks:
      raise self._refused('has no tick budget (%r)' % (self.ticks,))
    if self.ticks < 0 or (self.verb is Verb.WAIT and self.ticks == 0):
      infoSpec = """an action to %s is of ticks above 0%s, not %r"""
      own = '' if self.verb is Verb.WAIT else ', or 0 for the agent\'s own'
      raise ValueError(infoSpec % (self.verb.value, own, self.ticks))

  def __str__(self) -> str:
    """The action as a person says it: 'use MCBlocks.Lever at (5, 4, 7)'."""
    verb = self.verb
    if verb is Verb.WAIT:
      return 'wait %d ticks' % self.ticks
    if verb is Verb.CLOSE:
      return 'close'
    if verb is Verb.GO:
      said = 'go to %s' % where(self.place)
    elif verb in (Verb.TAKE, Verb.PUT):
      said = '%s %s' % (verb.value, named(self.thing))
    else:
      thing = 'the block' if self.thing is None else named(self.thing)
      said = '%s %s at %s' % (verb.value, thing, where(self.place))
    if self.ticks:
      said += ', within %d ticks' % self.ticks
    return said

  def _refused(self, why: str) -> TypeError:
    """The TypeError for an action its verb doesn't allow."""
    return TypeError('an action to %s %s' % (self.verb.value, why))

  def _checkThing(self, names: str) -> None:
    """TypeError unless the thing is as the verb names it."""
    thing = self.thing
    if thing is None:
      if names == _MUST:
        raise self._refused('names a thing, an mcdex member')
      return
    if names == _CANT:
      raise self._refused('names no thing (%r)' % (thing,))
    if not isinstance(thing, MCThing):
      raise self._refused('names its thing by an mcdex member, not %r' % (
        thing,))

  def _checkPlace(self, names: str) -> None:
    """TypeError unless the place is as the verb names it."""
    place = self.place
    if place is None:
      if names == _MUST:
        raise self._refused('names a place')
      return
    if names == _CANT:
      raise self._refused('names no place (%r)' % (place,))
    kinds = (BlockPos, Vec3) if self.verb is Verb.GO else (BlockPos,)
    if not isinstance(place, kinds):
      raise self._refused('names its place by a %s, not %r' % (
        ' or a '.join(each.__name__ for each in kinds), place))
