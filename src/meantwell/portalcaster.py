"""
PortalCaster: the routine that casts a nether portal from a lake of lava
with one bucket (SPEC.md 21.21). It plays the plan of a PortalCast move
by move on the body, by a player's means, and checks each by them: the
crosshair on the face before a click, the bucket empty after a pour and
full after a scoop. To stand somewhere and to dig are the agent's own
steps.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from mcdex import MCItems
from worktoy.desc import Field

from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3

from .castdoes import CastDoes
from .castmove import CastMove
from .portalcast import PortalCast
from .routine import Routine
from .words import met, named, where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, Optional

  from unittas.agent import Agent
  from unittas.perception import Perception

#  Which way each face of a block is turned
_NORMALS = {'up': (0, 1, 0), 'down': (0, -1, 0), 'south': (0, 0, 1),
            'north': (0, 0, -1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
#  What a bucket can be, by what it holds
_BUCKETS = (MCItems.Bucket, MCItems.WaterBucket, MCItems.LavaBucket)


class PortalCaster(Routine):
  """
  The caster of one agent. Beside the routine's five means it asks the
  body a tap of a key (the hotbar's, and use), its own inventory, and
  mcdex's names for what is in it; and the agent its walkTo and its
  breakBlock. It starts with a bucket of water, dirt and a flint and
  steel in its hotbar.

    caster = PortalCaster(agent, print)
    caster.cast(BlockPos(10, 64, 20), Vec3(12.5, 64.0, 26.5))
    # move 1 of 78: stand at (11.50, 64.00, 21.50) ...
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  How far from its eye a face or a source may be, in blocks (a
  #  survival player's reach is 4.5)
  REACH = 4.45
  #  How many ticks it lets pass after a click, for the game to answer
  AFTER = 3
  #  What it perceives about it at the lake: across, below, above
  LAKE = (5, 3, 0)
  #  How many sources it tries at the lake before it gives up
  TRIES = 4

  #  Fallback Variables

  #  Private Variables
  __agent__: Agent = None
  __say__: Callable = None
  #  Where it stands at the lake to fetch lava
  __lake__: Vec3 = None
  #  The move it is at, and how many the plan has: for what it says
  __at__: int = 0
  __of__: int = 0

  #  Public Variables
  agent = Field()
  lake = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @agent.GET
  def _getAgent(self) -> Agent:
    """The agent whose body it plays."""
    return self.__agent__

  @lake.GET
  def _getLake(self) -> Vec3:
    """Where it stands at the lake to fetch lava."""
    return self.__lake__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @lake.SET
  def _setLake(self, spot: Vec3) -> None:
    """Where it is to stand at the lake: a Vec3."""
    if not isinstance(spot, Vec3):
      raise TypeError('the lake\'s spot is a Vec3, not %r' % (spot,))
    self.__lake__ = spot

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, agent: Agent,
               say: Optional[Callable[[str], Any]] = None) -> None:
    """
    The caster of 'agent', saying each move it has made to 'say' (called
    with the line), if there is one.
    """
    Routine.__init__(self, agent.game)
    if say is not None and not callable(say):
      raise TypeError('whom it tells is called with each line, not %r' % (
        say,))
    self.__agent__ = agent
    self.__say__ = say

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def cast(self, origin: BlockPos, lake: Vec3) -> Perception:
    """
    Casts a portal at 'origin' with lava from the lake, and stands in
    it: every move of PortalCast(origin), in order, each said once it
    is made. What it perceives in the portal.

    Parameters
    ----------
    origin : BlockPos
      The cell the frame's left side stands in (PortalCast).
    lake : Vec3
      Where it stands at the lake: lava sources within its reach.

    Raises
    ------
    TesttimeError
      A move can't be made: named with its number, and why.
    """
    plan = PortalCast(origin).moves
    self.lake = lake
    self.__of__ = len(plan)
    seen = None
    for number, move in enumerate(plan, 1):
      self.__at__ = number
      seen = self.play(move)
      if self.__say__ is not None:
        self.__say__('move %d of %d: %s' % (number, len(plan), move))
    return seen

  def play(self, move: CastMove) -> Perception:
    """
    One move, made and checked by a player's means. What it perceives
    after.

    Raises
    ------
    TesttimeError
      It can't be made: the face out of reach or not what the crosshair
      meets, the bucket not as the move needs it or not as the move
      should leave it, no lava source in reach.
    """
    if not isinstance(move, CastMove):
      raise TypeError('the caster plays a CastMove, not %r' % (move,))
    does = move.does
    if does in (CastDoes.STAND, CastDoes.ENTER):
      return self.__agent__.walkTo(move.spot, 0.25)
    if does is CastDoes.DIG:
      return self.__agent__.breakBlock(move.pos)
    if does is CastDoes.FETCH_LAVA:
      return self._fetch(move)
    if does is CastDoes.SCOOP_WATER:
      return self._scoop(move, move.pos, MCItems.WaterBucket)
    if does is CastDoes.DIRT:
      return self._dirt(move)
    if does is CastDoes.LIGHT:
      self._chosen(move, (MCItems.FlintAndSteel,))
      return self._click(move)
    holds = (MCItems.WaterBucket if does is CastDoes.POUR_WATER
             else MCItems.LavaBucket)
    self._bucket(move, holds)
    seen = self._click(move)
    after = self._bucket(move, None)
    if after is not MCItems.Bucket:
      self._stop(move, seen, 'the bucket is still %s after the click' % (
        named(after),))
    return seen

  # ---------------------------------------------------------------- inside

  def _stop(self, move: CastMove, seen: Perception, why: str) -> None:
    """The TesttimeError for a move that can't be made, raised."""
    head = 'move %d of %d, ' % (self.__at__, self.__of__) if self.__of__ \
      else ''
    raise TesttimeError('cast', seen, '%s%s: %s' % (head, move, why))

  def _chosen(self, move: CastMove, members: tuple) -> Any:
    """
    The hotbar's slot holding one of the members chosen by its key, as
    a player knows its own inventory: which member it holds.
    """
    inventory = self.body.inventory()
    held = []
    for slot in range(9):
      stack = inventory.main[slot]
      if stack.empty:
        continue
      has = [each for each in self.body.membersOf(stack)
             if each in members]
      held.append('%s in %d' % (stack.id, slot + 1))
      if not has:
        continue
      if inventory.selected != slot:
        self.body.tap('key.hotbar.%d' % (slot + 1))
      return has[0]
    self._stop(move, self.body.perceive(*self.LOOK), 'no %s in the hotbar '
               '(%s)' % (' or '.join(named(each) for each in members),
                         ', '.join(held) or 'it is empty'))

  def _bucket(self, move: CastMove, holds: Any) -> Any:
    """
    Its bucket chosen: what it is (MCItems.Bucket, WaterBucket or
    LavaBucket). With 'holds' given, anything else stops the move.
    """
    has = self._chosen(move, _BUCKETS)
    if holds is not None and has is not holds:
      self._stop(move, self.body.perceive(*self.LOOK), 'the bucket is %s, '
                 'and the move needs %s' % (named(has), named(holds)))
    return has

  def _aim(self, move: CastMove, point: Vec3) -> Perception:
    """Its look turned to the point, within reach of its eye; what it
    perceives then."""
    seen = self.body.perceive(*self.LOOK)
    eye = seen.eye
    far = math.dist((eye.x, eye.y, eye.z), (point.x, point.y, point.z))
    if far > self.REACH:
      self._stop(move, seen, 'out of reach: %.2f blocks from its eye at '
                             '%s' % (far, where(eye)))
    across = math.hypot(point.x - eye.x, point.z - eye.z)
    yaw = math.degrees(math.atan2(-(point.x - eye.x), point.z - eye.z))
    pitch = math.degrees(math.atan2(-(point.y - eye.y), across))
    self.body.look(yaw, pitch)
    self.body.ticks(1)
    return self.body.perceive(*self.LOOK)

  def _click(self, move: CastMove) -> Perception:
    """
    One press of the use key on the move's face: its look turned to the
    face's middle, and the click made only with the crosshair on that
    face of that block. What it perceives after.
    """
    pos, normal = move.pos, _NORMALS[move.face]
    point = Vec3(*(each + 0.5 + 0.45 * turned for each, turned in zip(
      (pos.x, pos.y, pos.z), normal)))
    seen = self._aim(move, point)
    aim = seen.target
    if not (aim.kind == 'block' and aim.pos == pos and aim.face ==
            move.face):
      self._stop(move, seen, 'the crosshair meets %s%s, from its eye at '
                             '%s' % (met(aim), ', its %s face' % aim.face
                                     if aim.face else '', where(seen.eye)))
    self.body.tap('key.use')
    self.body.ticks(self.AFTER)
    return self.body.perceive(*self.LOOK)

  def _dirt(self, move: CastMove) -> Perception:
    """A block of dirt put on the move's face: the crosshair then meets
    the new block."""
    self._chosen(move, (MCItems.Dirt,))
    seen = self._click(move)
    into = move.pos.offset(*_NORMALS[move.face])
    if not (seen.target.kind == 'block' and seen.target.pos == into):
      self._stop(move, seen, 'the click placed nothing at %s: the '
                             'crosshair meets %s' % (where(into),
                                                     met(seen.target)))
    return seen

  def _scoop(self, move: CastMove, cell: BlockPos, holds: Any) -> Perception:
    """
    A source taken up: its empty bucket chosen, its look turned to the
    cell's middle, one press of the use key; the bucket then holds it.
    """
    self._bucket(move, MCItems.Bucket)
    self._aim(move, cell.center().above(0.5))
    self.body.tap('key.use')
    self.body.ticks(self.AFTER)
    seen = self.body.perceive(*self.LOOK)
    after = self._bucket(move, None)
    if after is not holds:
      self._stop(move, seen, 'the bucket is %s after the scoop at %s, '
                             'not %s' % (named(after), where(cell),
                                         named(holds)))
    return seen

  def _fetch(self, move: CastMove) -> Perception:
    """
    Lava fetched: to the lake's spot, and the nearest lava source in
    reach scooped; the next nearest if that took nothing, TRIES at most.
    """
    self._bucket(move, MCItems.Bucket)
    self.__agent__.walkTo(self.__lake__, 0.25)
    seen = self.body.perceive(*self.LAKE)
    eye = seen.eye
    sources = []
    for block in seen.blocks:
      if not block.id.endswith(':lava') or dict(block.state).get(
          'level', '0') != '0':
        continue
      middle = block.pos.center().above(0.5)
      far = math.dist((eye.x, eye.y, eye.z), (middle.x, middle.y, middle.z))
      if far <= self.REACH:
        sources.append((far, block.pos.x, block.pos.y, block.pos.z))
    if not sources:
      self._stop(move, seen, 'no lava source within %.2f blocks of its eye '
                             'at %s' % (self.REACH, where(eye)))
    for _, x, y, z in sorted(sources)[:self.TRIES]:
      self._aim(move, BlockPos(x, y, z).center().above(0.5))
      self.body.tap('key.use')
      self.body.ticks(self.AFTER)
      if self._bucket(move, None) is MCItems.LavaBucket:
        return self.body.perceive(*self.LOOK)
    self._stop(move, self.body.perceive(*self.LOOK), 'the bucket took no '
               'lava from the %d nearest sources' % min(len(sources),
                                                        self.TRIES))
