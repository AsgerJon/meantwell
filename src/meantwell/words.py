"""
The 'words' module is how things are said (SPEC.md 21.3: it says what it
did and saw), the same wherever a line goes: a report, a terminal, the
chat.

- named(member): an mcdex member, 'MCBlocks.Lever'.
- where(place): a place, a block's or a point's.
- stack(item), stacks(items): what a slot holds, and what several do.
- met(target): what the crosshair met.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from unittas.values import BlockPos

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


def named(member: Any) -> str:
  """An mcdex member as it is said: 'MCBlocks.Lever'."""
  return '%s.%s' % (type(member).__name__, member.name)


def where(place: Any) -> str:
  """A place as it is said: a block's whole, a point's to two places."""
  if isinstance(place, BlockPos):
    return '(%d, %d, %d)' % (place.x, place.y, place.z)
  return '(%.2f, %.2f, %.2f)' % (place.x, place.y, place.z)


def stack(item: Any) -> str:
  """
  A stack as it is said: its count and the game's own id for it, with
  its meta where it has one above 0 (1.13 on it has none, -1).
  """
  meta = ':%d' % item.meta if item.meta > 0 else ''
  return '%d %s%s' % (item.count, item.id, meta)


def stacks(items: Any) -> str:
  """The stacks that aren't empty, in their order; 'nothing' for none."""
  return ', '.join(stack(each) for each in items
                   if not each.empty) or 'nothing'


def met(target: Any) -> str:
  """What the crosshair met, as it is said."""
  if target.kind == 'block':
    return '%s at %s' % (target.id, where(target.pos))
  if target.kind == 'entity':
    return '%s (entity %d)' % (target.type, target.entity)
  return 'nothing within reach'
