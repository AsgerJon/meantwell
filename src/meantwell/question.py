"""
Question: what an examination can ask the agent (SPEC.md 21.7 step 3),
each answered by the agent's own means alone: never by command, and
never from the server's side (SPEC.md 21.4). Called with its
examination's parts, a question makes the examination (SPEC.md 21.19
S1).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import Kee, KeeNum

from . import told

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from .examination import Examination


class Question(KeeNum):
  """
  An examination's question, its value the word a person says it by.
  Called, it makes its examination.

    Question.INVENTORY()
    Question.CONTENTS()
    Question.IDENTIFY(stone, among=(MCBlocks.Stone, MCBlocks.Bedrock))
  """
  #  the mcdex members in its own inventory, as a player knows its own
  INVENTORY = Kee[str]('inventory')
  #  what the open container holds, as its screen shows it
  CONTENTS = Kee[str]('contents')
  #  what a block is, from its looks alone
  IDENTIFY = Kee[str]('identify')

  def __call__(self, *parts: Any, among: Any = ()) -> Examination:
    """
    The examination that asks this, the same value as Examination(asks,
    place, among) made by hand.

    Parameters
    ----------
    *parts
      For what a block is: its place (a BlockPos), or a thing with its
      own place, whose place it is. None for the others.
    among
      For what a block is: the candidates, mcdex members.

    Raises
    ------
    TypeError
      Two places, a part that is no place and has none, or what the
      examination itself refuses.
    """
    #  late: the examination takes its question from this module
    from .examination import Examination
    what = 'the examination \'%s\'' % self.value
    place = None
    for part in parts:
      both = told.handle(part)
      if both is None:
        _, found, _ = told.parts(what, (part,))
      else:
        found = both[1]
      if found is None or place is not None:
        infoSpec = """%s is told one place, or one thing with its own
        place, not %r"""
        raise TypeError(' '.join((infoSpec % (what, parts)).split()))
      place = found
    return Examination(self, place, tuple(among))
