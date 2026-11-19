"""
LakeCast: the plan of a nether portal cast in the edge of a lake of
lava, as a speedrunner's beginner casts it (SPEC.md 21.24; Asger's
clips, and his own drawings of it). A value, with no game in it: a
caster plays it in a game, a world of blocks plays it in the tests.

The frame stands in the lake's own edge row, a block down in it. Along
the shore x, out into the lake z; the shore's rim is the row z -1, its
top the ground; the lake's top layer lies at y -1 from z 0 on.

1. **The opening.** A block is put out into the edge row (on the lake's
   floor, through the lava), the water is poured against its side, and
   the block is dug out again. The water lies in two cells; the lava at
   each end of them is obsidian, the lowest block of each side.
2. **The bottom.** In a lake one deep the two blocks under the water are
   dug out, and lava put in their place: obsidian, under water.
3. **The mold.** Three blocks under its own feet behind the right side,
   and one out from the top of them over that side: the upside down L,
   whose arm is the frame's upper right corner. Two blocks on the rim
   behind the left side and the inside's left half. A hole in the floor
   behind those two.
4. **The water** is taken up and poured against the pillar's top block,
   over the gap between the pillar and the two blocks. It falls there
   and goes into the frame's inside; it runs off its own height over the
   two blocks and into the frame's top right cell, and falls from there.
   The two blocks keep it off the lake (without them, in the tests'
   world, it turns 53 cells of the lake to obsidian).
5. **Six pours** of lava scooped from the lake where it stands: two up
   the left side, two up the right, the top right against the arm, the
   top left against that. Then the water is taken up, the bottom is lit,
   and it steps down into the portal.

It is for a lake one deep and at least 11 cells along the shore by 3
out, with a level floor about it: the MCSR practice map's surface lava
level. Its 44 moves and where it stands for each were found by trying
every place to stand in the tests' world (SPEC.md 21.24); the game has
not played it yet.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZData, EZField

from unittas.values import BlockPos, Vec3

from .castdoes import CastDoes
from .castmove import CastMove

#  The frame in the cast's own places: its bottom, its two sides (the
#  lowest block of each at the lake's level), its top; and its inside
BOTTOM = ((3, -2, 0), (4, -2, 0))
LEFT = ((2, -1, 0), (2, 0, 0), (2, 1, 0))
RIGHT = ((5, -1, 0), (5, 0, 0), (5, 1, 0))
TOP = ((3, 2, 0), (4, 2, 0))
INSIDE = tuple((x, y, 0) for x in (3, 4) for y in (-1, 0, 1))
#  The lake's cells the opening turns to obsidian: the sides' lowest
#  blocks, and the two beyond the water
CRUSTS = ((2, -1, 0), (5, -1, 0), (3, -1, 1), (4, -1, 1))
#  The mold: the pillar, its arm, the two blocks; and the hole
PILLAR = ((5, 0, -1), (5, 1, -1), (5, 2, -1))
ARM = (5, 2, 0)
BLOCKS = ((2, 0, -1), (3, 0, -1))
HOLE = (3, -1, -2)
#  Every move, in order: (what it does, the block, its face, the spot)
_MOVES = (
  ('STAND', None, '', (3.5, 0.0, -0.5)),
  ('DIRT', (3, -2, 0), 'up', None),
  ('STAND', None, '', (4.5, 0.0, -0.5)),
  ('POUR_WATER', (3, -1, 0), 'east', None),
  ('DIG', (3, -1, 0), '', None),
  ('LEAN', None, 'south', None),
  ('DIG', (3, -2, 0), '', None),
  ('DIG', (4, -2, 0), '', None),
  ('SCOOP_LAVA', (5, -1, 1), '', None),
  ('POUR_LAVA', (3, -3, 0), 'up', None),
  ('SCOOP_LAVA', (6, -1, 0), '', None),
  ('POUR_LAVA', (4, -3, 0), 'up', None),
  ('STAND', None, '', (5.5, 0.0, -0.5)),
  ('PILLAR', None, '', None),
  ('PILLAR', None, '', None),
  ('PILLAR', None, '', None),
  ('LEAN', None, 'south', None),
  ('DIRT', (5, 2, -1), 'south', None),
  ('STAND', None, '', (5.5, 0.0, 0.5)),
  ('DIRT', (2, -1, -1), 'up', None),
  ('DIRT', (3, -1, -1), 'up', None),
  ('LEAN', None, 'west', None),
  ('DIG', (3, -1, -2), '', None),
  ('SCOOP_WATER', (4, -1, 0), '', None),
  ('POUR_WATER', (5, 2, -1), 'west', None),
  ('SCOOP_LAVA', (4, -1, 2), '', None),
  ('POUR_LAVA', (2, -1, 0), 'up', None),
  ('SCOOP_LAVA', (6, -1, 1), '', None),
  ('POUR_LAVA', (2, 0, 0), 'up', None),
  ('STAND', None, '', (4.5, 0.0, -0.5)),
  ('LEAN', None, 'south', None),
  ('SCOOP_LAVA', (2, -1, 1), '', None),
  ('POUR_LAVA', (5, -1, 0), 'up', None),
  ('SCOOP_LAVA', (3, -1, 2), '', None),
  ('POUR_LAVA', (5, 0, 0), 'up', None),
  ('SCOOP_LAVA', (5, -1, 2), '', None),
  ('POUR_LAVA', (5, 2, 0), 'west', None),
  ('STAND', None, '', (3.5, 0.0, 1.5)),
  ('SCOOP_LAVA', (2, -1, 2), '', None),
  ('POUR_LAVA', (4, 2, 0), 'west', None),
  ('STAND', None, '', (4.5, 0.0, -0.5)),
  ('SCOOP_WATER', (4, 2, -1), '', None),
  ('LIGHT', (4, -2, 0), 'up', None),
  ('ENTER', None, '', (3.5, -1.0, 0.5)),
)


class LakeCast(EZData, frozen=True):
  """
  The plan of a cast at 'origin' (a BlockPos: the cell over the lake's
  edge row at the cast's own x 0; the frame stands from x 2 to x 5).

    cast = LakeCast(BlockPos(-3, 16, 35))
    cast.frame      # the ten cells that are to be obsidian
    cast.interior   # the six that are to be free
    cast.moves      # each CastMove, in order
    cast.lake       # where a lake lies that suits it (for a scene)
    cast.crusts     # the lake's cells it means to turn to obsidian
    cast.blocks     # how many blocks it puts down
  """

  origin = EZField[BlockPos]()

  def at(self, x: int, y: int, z: int) -> BlockPos:
    """The block at the cast's own place (x, y, z)."""
    return self.origin.offset(x, y, z)

  def spot(self, x: float, y: float, z: float) -> Vec3:
    """The point at the cast's own place (x, y, z)."""
    origin = self.origin
    return Vec3(origin.x + x, origin.y + y, origin.z + z)

  @property
  def frame(self) -> tuple:
    """The ten cells that are to be obsidian."""
    return tuple(self.at(*cell) for cell in BOTTOM + LEFT + RIGHT + TOP)

  @property
  def interior(self) -> tuple:
    """The six cells inside the frame, which are to be free."""
    return tuple(self.at(*cell) for cell in INSIDE)

  @property
  def inside(self) -> Vec3:
    """Where one stands in the portal: on its bottom, in its left half."""
    return self.spot(3.5, -1.0, 0.5)

  @property
  def start(self) -> Vec3:
    """Where it begins: on the floor, two and a half blocks from the
    lake, before the frame's left half."""
    return self.spot(3.5, 0.0, -2.5)

  @property
  def lake(self) -> tuple:
    """The cells of a lake that suits the plan, 11 along the shore by
    11 out and one deep: for a scene's setup, and for the tests."""
    return tuple(self.at(x, -1, z) for x in range(-3, 8)
                 for z in range(0, 11))

  @property
  def crusts(self) -> tuple:
    """The lake's cells the opening turns to obsidian, and means to."""
    return tuple(self.at(*cell) for cell in CRUSTS)

  @property
  def blocks(self) -> int:
    """How many blocks it puts down: the opening's, the pillar's three,
    its arm, the two."""
    return sum(1 for name, _, _, _ in _MOVES if name in ('DIRT', 'PILLAR'))

  @property
  def moves(self) -> tuple:
    """Every move of the cast, in order."""
    made = []
    for name, cell, face, spot in _MOVES:
      made.append(CastMove(
        CastDoes[name], None if cell is None else self.at(*cell), face,
        None if spot is None else self.spot(*spot)))
    return tuple(made)
