"""
Verb: the actions an instruction can name (SPEC.md 21.7 step 3), each
one of the agent's own steps. A closed set: a verb comes in with the
skill that carries it out.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class Verb(KeeNum):
  """An action's verb, its value the word a person says it by."""
  GO = Kee[str]('go')
  USE = Kee[str]('use')
  BREAK = Kee[str]('break')
  PLACE = Kee[str]('place')
  OPEN = Kee[str]('open')
  TAKE = Kee[str]('take')
  PUT = Kee[str]('put')
  CLOSE = Kee[str]('close')
  WAIT = Kee[str]('wait')
