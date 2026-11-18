"""
Verb: the actions an instruction can name (SPEC.md 21.7 step 3), each
one of the agent's own steps. A closed set: a verb comes in with the
skill that carries it out. Called with its action's parts, a verb makes
the action (SPEC.md 21.19 S1): the short words a series is written in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import Kee, KeeNum

from . import told

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from .action import Action


class Verb(KeeNum):
  """
  An action's verb, its value the word a person says it by. Called, it
  makes its action, each part told by its kind (told.py): a thing with
  its own place, an mcdex member, a place; for a wait, its ticks.

    Verb.OPEN(chest)                  # a scene's thing: what, and where
    Verb.USE(lever, ticks=200)
    Verb.PLACE(MCItems.Stone, BlockPos(1, 4, 1))
    Verb.TAKE(MCItems.PinkWool)
    Verb.GO(Vec3(6.5, 4.0, 4.5))
    Verb.WAIT(40)
    Verb.CLOSE()
  """
  GO = Kee[str]('go')
  USE = Kee[str]('use')
  BREAK = Kee[str]('break')
  PLACE = Kee[str]('place')
  OPEN = Kee[str]('open')
  TAKE = Kee[str]('take')
  PUT = Kee[str]('put')
  CLOSE = Kee[str]('close')
  WAIT = Kee[str]('wait')

  def __call__(self, *parts: Any, ticks: int = 0) -> Action:
    """
    The action of this verb with these parts, the same value as
    Action(verb, thing, place, ticks) made by hand.

    Parameters
    ----------
    *parts
      A thing with its own place, an mcdex member, a BlockPos or a
      Vec3; for a wait, a whole number of ticks.
    ticks : int
      The step's tick budget (0: the agent's own), or a wait's length.

    Raises
    ------
    TypeError
      Two parts of a kind, a part of another kind, a whole number for
      anything but a wait's length, or what the action itself refuses.
    """
    #  late: the action takes its verb from this module
    from .action import Action
    what = 'an action to %s' % self.value
    thing, place, number = told.parts(what, parts)
    if number is not None:
      if self is not type(self).WAIT:
        infoSpec = """%s takes its tick budget as ticks=, not as %r
        among its parts"""
        raise TypeError(' '.join((infoSpec % (what, number)).split()))
      if ticks:
        infoSpec = """%s is told its length once, not as %r and as
        ticks=%r"""
        raise TypeError(' '.join((infoSpec % (what, number,
                                              ticks)).split()))
      ticks = number
    return Action(self, thing, place, ticks)
