"""
Question: what an examination can ask the agent (SPEC.md 21.7 step 3),
each answered by the agent's own means alone: never by command, and
never from the server's side (SPEC.md 21.4).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class Question(KeeNum):
  """An examination's question, its value the word a person says it by."""
  #  the mcdex members in its own inventory, as a player knows its own
  INVENTORY = Kee[str]('inventory')
  #  what the open container holds, as its screen shows it
  CONTENTS = Kee[str]('contents')
  #  what a block is, from its looks alone
  IDENTIFY = Kee[str]('identify')
