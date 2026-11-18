"""
CastSim: a world of blocks a portal cast's plan is played in, without a
game (not a test module itself; SPEC.md 21.21). It holds the plan to how
water runs in the game and to what a player can do from where it stands.

Water runs as the game's own rule has it (the first cast in the practice
game showed that falling straight was a belief, not the rule):

- A source, or water that fell, lying on something solid runs to its
  sides, a level less each block, 7 at most.
- It runs only towards the nearest way down within 4 blocks, if there is
  one (so a hole dug beside it takes it all); else every open way.
- With nothing under it, it falls. A source runs to its open sides too
  once its fall stands under it; water that only runs does not.
- With its source gone it runs dry.
- A lava source with water beside it or above it is obsidian, at once;
  poured into water it takes the water's place and is obsidian. One left
  with neither, and not held in on all sides, runs after 30 ticks.

A click needs its block there, its face turned to the eye, within reach,
and nothing solid between; what it places lands in the cell beyond the
face. A scoop takes the first source its ray meets. Each is held to this
from where the robot is to stand and from a quarter of a block to each
side of it: it doesn't stand to the hair. One bucket: it holds water,
lava or nothing, and each move needs it as it must be.

Whatever goes wrong is kept in 'faults', each with the move it happened
at. A plan is sound when it ends with none.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import Optional

from meantwell.castdoes import CastDoes
from meantwell.castmove import CastMove
from unittas.values import BlockPos, Vec3

NORMALS = {'up': (0, 1, 0), 'down': (0, -1, 0), 'south': (0, 0, 1),
           'north': (0, 0, -1), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
SIDES = ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))
SOLID = ('ground', 'dirt', 'obsidian')
#  How long each move takes, in ticks, near enough
TAKES = {CastDoes.STAND: 40, CastDoes.DIG: 20, CastDoes.FETCH_LAVA: 120,
         CastDoes.ENTER: 40}
#  How far from where it is to stand the robot may stand, each way
OFF = ((0.0, 0.0), (0.25, 0.0), (-0.25, 0.0), (0.0, 0.25), (0.0, -0.25))


class CastSim:
  """
  The world: ground up to 'ground' (the y of its top blocks), a lake of
  lava in the cells 'lake', and the robot at 'start' with a bucket of
  water and 'dirt' blocks of dirt. 'frame' and 'interior' are the cells
  a lit portal needs (obsidian, and free); 'shore' is where it stands to
  fetch lava. 'water' holds every cell with water in it and how much (8:
  a source, or water that fell).
  """

  REACH, EYE = 4.5, 1.62
  LAVA_RUNS = 30
  #  How far from the frame water may lie on the ground, in blocks
  YARD = 2

  def __init__(self, ground: int, lake: tuple, start: Vec3, frame: tuple,
               interior: tuple, shore: Vec3, dirt: int = 64) -> None:
    self.ground = ground
    self.blocks = {self._key(cell): 'lava' for cell in lake}
    self.lake = set(self.blocks)
    self.dug = set(self.lake)
    self.sources = set()
    self.water = {}
    self.poured = {}
    self.pos = start
    self.shore = shore
    self.frame = tuple(self._key(cell) for cell in frame)
    self.interior = tuple(self._key(cell) for cell in interior)
    self.bucket = 'water'
    self.dirt = dirt
    self.tick = 0
    self.fetches = 0
    self.lit = False
    self.entered = False
    self.faults = []
    self.played = 0
    #  every cell water ever was in, and the lake's cells it turned
    self.wetted = set()
    self.crusted = set()

  # --------------------------------------------------------------- blocks

  @staticmethod
  def _key(cell: object) -> tuple:
    return (cell.x, cell.y, cell.z) if isinstance(cell, BlockPos) else cell

  def kind(self, cell: tuple) -> str:
    """What is in the cell: a block's kind, 'ground', or 'air'."""
    if cell in self.blocks:
      return self.blocks[cell]
    if cell[1] <= self.ground and cell not in self.dug:
      return 'ground'
    return 'air'

  def solid(self, cell: tuple) -> bool:
    return self.kind(cell) in SOLID

  def free(self, cell: tuple) -> bool:
    """Whether a player can be in the cell, water or none."""
    return self.kind(cell) in ('air', 'portal')

  # ---------------------------------------------------------------- water

  def _hole(self, cell: tuple) -> bool:
    """Whether water in the cell has a way down."""
    return not self.solid((cell[0], cell[1] - 1, cell[2]))

  def _open(self, cell: tuple) -> bool:
    """Whether water can run into the cell."""
    return not self.solid(cell) and cell not in self.sources and (
      self.kind(cell) != 'lava')

  def _slope(self, cell: tuple, depth: int, back: tuple) -> int:
    """How far the nearest way down is from the cell, 4 blocks at most
    (1000: none)."""
    best = 1000
    for dx, _, dz in SIDES:
      if (dx, dz) == back:
        continue
      near = (cell[0] + dx, cell[1], cell[2] + dz)
      if not self._open(near):
        continue
      if self._hole(near):
        return depth
      if depth < 4:
        best = min(best, self._slope(near, depth + 1, (-dx, -dz)))
    return best

  def _ways(self, cell: tuple) -> list:
    """The cells beside it water runs to: those towards the nearest way
    down, or every open one."""
    least, ways = 1000, []
    for dx, _, dz in SIDES:
      near = (cell[0] + dx, cell[1], cell[2] + dz)
      if not self._open(near):
        continue
      far = 0 if self._hole(near) else self._slope(near, 1, (-dx, -dz))
      if far < least:
        least, ways = far, []
      if far <= least:
        ways.append(near)
    return ways

  def _turn(self) -> bool:
    """Lava beside water, or under it, is obsidian; whether any was."""
    turned = False
    for cell, kind in list(self.blocks.items()):
      if kind != 'lava':
        continue
      x, y, z = cell
      about = [(x + dx, y, z + dz) for dx, _, dz in SIDES] + [(x, y + 1, z)]
      if any(each in self.water for each in about):
        self.blocks[cell] = 'obsidian'
        turned = True
        if cell in self.lake:
          self.crusted.add(cell)
    return turned

  def flow(self) -> None:
    """The water run until it lies still."""
    for _ in range(200):
      before = dict(self.water)
      #  what each cell of running water has left
      for cell in sorted(self.water):
        if cell in self.sources:
          continue
        x, y, z = cell
        if self.solid(cell):
          del self.water[cell]
        elif (x, y + 1, z) in self.water:
          self.water[cell] = 8
        else:
          most = max((self.water.get((x + dx, y, z + dz), 0)
                      for dx, _, dz in SIDES), default=0)
          #  water that fell runs on as a source does
          if most - 1 > 0:
            self.water[cell] = most - 1
          else:
            del self.water[cell]
      #  where each runs to
      for cell in sorted(self.water):
        if cell not in self.water:
          continue
        x, y, z = cell
        below = (x, y - 1, z)
        if not self.solid(below) and self.kind(below) != 'lava':
          if below not in self.water:
            self.water[below] = 8
            continue
          if cell not in self.sources:
            continue
        left = 7 if self.water[cell] == 8 else self.water[cell] - 1
        if left <= 0:
          continue
        for near in self._ways(cell):
          if self.water.get(near, 0) < left:
            self.water[near] = left
      self._turn()
      self.wetted |= set(self.water)
      if self.water == before:
        return
    raise RuntimeError('the water never came to lie still')

  # ---------------------------------------------------------------- play

  def play(self, moves: tuple) -> list:
    """Each move in turn, to the first that can't be made; the faults."""
    for move in moves:
      before = len(self.faults)
      {CastDoes.STAND: self._stand, CastDoes.DIG: self._dig,
       CastDoes.DIRT: self._click, CastDoes.POUR_WATER: self._click,
       CastDoes.POUR_LAVA: self._click, CastDoes.LIGHT: self._click,
       CastDoes.SCOOP_WATER: self._scoop,
       CastDoes.FETCH_LAVA: self._fetch,
       CastDoes.ENTER: self._enter}[move.does](move)
      self.tick += TAKES.get(move.does, 8)
      self.flow()
      self._settle(move)
      if len(self.faults) > before:
        break
      self.played += 1
    return self.faults

  def _fault(self, move: CastMove, why: str) -> None:
    self.faults.append('%s: %s' % (move, why))

  def _eyes(self) -> list:
    """Its eye, where it is to stand and a quarter block each way."""
    return [(self.pos.x + dx, self.pos.y + self.EYE, self.pos.z + dz)
            for dx, dz in OFF]

  def _settle(self, move: CastMove) -> None:
    """Lava that no water came to, runs; and water has run off when it
    lies on the ground further than YARD from the frame, or reached the
    lake."""
    if self.crusted:
      self._fault(move, 'the water reached the lake: %d of its cells are '
                        'obsidian' % len(self.crusted))
    far = [cell for cell in self.water
           if cell[1] == self.ground + 1 and self.frame and min(
             max(abs(cell[0] - each[0]), abs(cell[2] - each[2]))
             for each in self.frame) > self.YARD]
    if far:
      self._fault(move, 'the water runs off over the ground: %d cells '
                        'of it more than %d from the frame' % (
                          len(far), self.YARD))
    for cell, kind in list(self.blocks.items()):
      if kind != 'lava' or cell in self.lake:
        continue
      x, y, z = cell
      inside = self.solid((x, y - 1, z)) and all(
        self.solid((x + dx, y, z + dz)) for dx, _, dz in SIDES)
      if not inside and self.tick - self.poured[cell] > self.LAVA_RUNS:
        self._fault(move, 'the lava at %r ran: no water came to it in %d '
                          'ticks' % (cell, self.tick - self.poured[cell]))

  def _stand(self, move: CastMove) -> None:
    spot = move.spot
    cell = (math.floor(spot.x), math.floor(spot.y), math.floor(spot.z))
    above = (cell[0], cell[1] + 1, cell[2])
    below = (cell[0], cell[1] - 1, cell[2])
    if not (self.free(cell) and self.free(above) and self.solid(below)):
      return self._fault(move, 'nowhere to stand there: %s on %s under %s'
                         % (self.kind(cell), self.kind(below),
                            self.kind(above)))
    if cell in self.water:
      return self._fault(move, 'it would stand in water')
    self.pos = spot
    return None

  def _sight(self, eye: tuple, point: tuple,
             last: Optional[tuple] = None) -> tuple:
    """
    The cells the eye's ray to the point goes through, in order, up to
    the first solid one (kept as the last) or the cell 'last'.
    """
    far = math.dist(eye, point)
    seen = []
    for at in range(int(far / 0.01) + 1):
      part = min(1.0, at * 0.01 / far) if far else 1.0
      cell = tuple(math.floor(eye[i] + (point[i] - eye[i]) * part)
                   for i in range(3))
      if not seen or seen[-1] != cell:
        seen.append(cell)
        if self.solid(cell) or cell == last:
          break
    return tuple(seen)

  def _faced(self, move: CastMove) -> Optional[str]:
    """Why the move's face can't be clicked from where it stands (or a
    quarter block off), or None."""
    support = self._key(move.pos)
    normal = NORMALS[move.face]
    into = tuple(support[i] + normal[i] for i in range(3))
    point = tuple(support[i] + 0.5 + 0.45 * normal[i] for i in range(3))
    if not self.solid(support):
      return 'nothing to click: %s is there' % (self.kind(support),)
    for eye in self._eyes():
      shows = sum((eye[i] - support[i] - 0.5) * normal[i]
                  for i in range(3))
      if shows <= 0.5:
        return 'the face is turned away from the eye at %r' % (eye,)
      if math.dist(eye, point) > self.REACH:
        return 'out of reach: %.2f blocks from %r' % (
          math.dist(eye, point), eye)
      seen = self._sight(eye, point)
      if seen[-1] != support or len(seen) < 2 or seen[-2] != into:
        return 'not in sight from %r: the ray meets %s at %r' % (
          eye, self.kind(seen[-1]), seen[-1])
    return None

  def _click(self, move: CastMove) -> None:
    support = self._key(move.pos)
    normal = NORMALS[move.face]
    into = tuple(support[i] + normal[i] for i in range(3))
    why = self._faced(move)
    if why is not None:
      return self._fault(move, why)
    does = move.does
    if does is CastDoes.LIGHT:
      return self._light(move)
    if not self.free(into):
      return self._fault(move, 'no room: %s is at %r' % (
        self.kind(into), into))
    if does is CastDoes.DIRT:
      if self.dirt < 1:
        return self._fault(move, 'no dirt left')
      self.dirt -= 1
      self.blocks[into] = 'dirt'
      return None
    holds = 'water' if does is CastDoes.POUR_WATER else 'lava'
    if self.bucket != holds:
      return self._fault(move, 'the bucket holds %s' % self.bucket)
    self.bucket = 'nothing'
    if does is CastDoes.POUR_WATER:
      if into in self.sources:
        return self._fault(move, 'water is there already')
      self.sources.add(into)
      self.water[into] = 8
      return None
    #  lava: in water, or with water beside it or above it, obsidian
    x, y, z = into
    about = [(x + dx, y, z + dz) for dx, _, dz in SIDES] + [(x, y + 1, z)]
    wet = into in self.water or any(each in self.water for each in about)
    self.sources.discard(into)
    self.water.pop(into, None)
    self.blocks[into] = 'obsidian' if wet else 'lava'
    self.poured[into] = self.tick
    return None

  def _light(self, move: CastMove) -> None:
    cast = [cell for cell in self.frame if self.kind(cell) != 'obsidian']
    full = [cell for cell in self.interior
            if not self.free(cell) or cell in self.water]
    if cast or full:
      return self._fault(move, 'no portal: %d of the frame not obsidian, '
                               '%d of its inside not free' % (len(cast),
                                                              len(full)))
    self.lit = True
    for cell in self.interior:
      self.blocks[cell] = 'portal'
    return None

  def _scoop(self, move: CastMove) -> None:
    cell = self._key(move.pos)
    if self.bucket != 'nothing':
      return self._fault(move, 'the bucket holds %s' % self.bucket)
    if cell not in self.sources:
      return self._fault(move, 'no water source there')
    point = tuple(each + 0.5 for each in cell)
    for eye in self._eyes():
      if math.dist(eye, point) > self.REACH:
        return self._fault(move, 'out of reach: %.2f blocks from %r' % (
          math.dist(eye, point), eye))
      met = None
      for met in self._sight(eye, point, cell):
        if met in self.sources or self.kind(met) == 'lava':
          break
      if met != cell:
        return self._fault(move, 'from %r the ray meets %s at %r first' % (
          eye, 'water' if met in self.sources else self.kind(met), met))
    self.sources.discard(cell)
    del self.water[cell]
    self.bucket = 'water'
    return None

  def _dig(self, move: CastMove) -> None:
    cell = self._key(move.pos)
    if self.kind(cell) not in ('ground', 'dirt'):
      return self._fault(move, 'it can\'t dig %s' % self.kind(cell))
    centre = tuple(each + 0.5 for each in cell)
    far = max(math.dist(eye, centre) for eye in self._eyes())
    if far > 3.5:
      return self._fault(move, 'too far to dig without walking: %.2f' % (
        far,))
    if cell in self.blocks:
      del self.blocks[cell]
    else:
      self.dug.add(cell)
    return None

  def _fetch(self, move: CastMove) -> None:
    if self.bucket != 'nothing':
      return self._fault(move, 'the bucket holds %s' % self.bucket)
    self.pos = self.shore
    eye = self._eyes()[0]
    near = sorted((math.dist(eye, tuple(each + 0.5 for each in cell)), cell)
                  for cell in self.lake if self.blocks.get(cell) == 'lava')
    if not near or near[0][0] > 4.4:
      return self._fault(move, 'no lava within reach of the shore')
    del self.blocks[near[0][1]]
    self.bucket = 'lava'
    self.fetches += 1
    return None

  def _enter(self, move: CastMove) -> None:
    spot = move.spot
    cell = (math.floor(spot.x), math.floor(spot.y), math.floor(spot.z))
    if self.kind(cell) != 'portal':
      return self._fault(move, 'no portal to stand in: %s' % (
        self.kind(cell),))
    self.entered = True
    self.pos = spot
    return None
