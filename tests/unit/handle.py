"""
Handle: a thing with its own place, as a scene's Thing is in unitTAS
(not a test module itself): an mcdex 'member' and the 'pos' it is at.
Its truth is never asked: in unitTAS that is an examination by command,
so here it fails whoever asks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any

from unittas.values import BlockPos


class Handle:
  """The thing 'member' at 'pos'."""

  def __init__(self, member: Any, pos: BlockPos) -> None:
    self.member = member
    self.pos = pos

  def __bool__(self) -> bool:
    raise AssertionError('a thing\'s truth was asked: in unitTAS that is '
                         'an examination by command')
