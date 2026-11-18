"""
PortalCast: the plan of a nether portal cast beside a lake of lava with
one bucket (SPEC.md 21.21): where its frame stands, and every move that
makes it, in order. A value, with no game in it: the caster plays it in
a game, a world of blocks plays it in the tests.

It is cast as a speedrunner casts one (Asger's clip, SPEC.md 21.21): the
water runs from the top of a pillar of dirt, lava is poured against the
pillar into the falling water and is obsidian at once, and a hole dug
at the pillar's foot takes the water, so that it doesn't run off over
the ground.

- The pillar is the portal's own inside, filled with dirt: two wide,
  three high. The water poured on its top runs off it to the nearest
  way down: over one side of the frame, and before and behind.
- A trench before the frame and one behind it take what falls there,
  and what lands at a side's foot runs round the corner into them.
- The water is poured on the left half of the pillar's top for the left
  side, then moved to the right half for the right side. Each block of
  a side is lava poured against the pillar's face, into the fall.
- The top: lava on the pillar's top beside the water, then into the
  water's own cell. That takes the last of the water.
- The bottom is sunk in the ground and cast first, in the front trench
  with the water lying in it. A platform of dirt, two high with a step,
  is what it stands on to finish the pillar and to pour on its top.

Its places are counted from its 'origin', the cell the left side's
lowest block stands in: x along the frame (east), y up from where one
stands, z towards the side it is built from (south).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.ezdata import EZData, EZField

from unittas.values import BlockPos, Vec3

from .castdoes import CastDoes
from .castmove import CastMove

#  The frame, in the cast's own places: its bottom, its sides from the
#  ground up, its top; and what is inside it
BOTTOM = ((1, -1, 0), (2, -1, 0))
LEFT = ((0, 0, 0), (0, 1, 0), (0, 2, 0))
RIGHT = ((3, 0, 0), (3, 1, 0), (3, 2, 0))
TOP = ((1, 3, 0), (2, 3, 0))
INSIDE = tuple((x, y, 0) for x in (1, 2) for y in (0, 1, 2))


class PortalCast(EZData, frozen=True):
  """
  The plan of a cast at 'origin' (a BlockPos: the cell the left side's
  lowest block stands in, the ground under it). The ground about it is
  to be level and bare: 3 blocks to each side of the frame, 3 behind it
  and 6 before it; and the lake's lava within reach of 'shore'.

    cast = PortalCast(BlockPos(10, 64, 20))
    cast.frame      # the ten cells that are to be obsidian
    cast.interior   # the six that are to be free
    cast.moves      # each CastMove, in order
    cast.shore      # where it stands to fetch lava
    cast.lake       # where a lake lies that suits it (for a scene)
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
    """Where one stands in the portal: on its bottom, in the middle."""
    return self.spot(2.0, 0.0, 0.5)

  @property
  def shore(self) -> Vec3:
    """Where it stands to fetch lava: before the lake, behind where it
    builds."""
    return self.spot(2.0, 0.0, 5.5)

  @property
  def lake(self) -> tuple:
    """The cells of a lake that suits the plan, six by four and two
    deep, its near edge a block and a half from 'shore': for a scene's
    setup, and for the tests."""
    return tuple(self.at(x, -1 - down, z) for x in range(-1, 5)
                 for z in range(7, 11) for down in range(2))

  @property
  def moves(self) -> tuple:
    """Every move of the cast, in order."""
    made = []

    def stand(x: float, y: float, z: float) -> None:
      made.append(CastMove(CastDoes.STAND, spot=self.spot(x, y, z)))

    def dig(*cell: int) -> None:
      made.append(CastMove(CastDoes.DIG, self.at(*cell)))

    def click(does: CastDoes, face: str, *cell: int) -> None:
      made.append(CastMove(does, self.at(*cell), face))

    def dirt(face: str, *cell: int) -> None:
      click(CastDoes.DIRT, face, *cell)

    def water(face: str, *cell: int) -> None:
      click(CastDoes.POUR_WATER, face, *cell)

    def lava(face: str, *cell: int) -> None:
      click(CastDoes.POUR_LAVA, face, *cell)

    def scoop(*cell: int) -> None:
      made.append(CastMove(CastDoes.SCOOP_WATER, self.at(*cell)))

    def fetch() -> None:
      made.append(CastMove(CastDoes.FETCH_LAVA))

    front, left, right = (2.0, 0.0, 2.5), (-0.5, 0.0, 2.5), (4.5, 0.0, 2.5)
    up1, up2 = (1.5, 2.0, 2.5), (2.5, 2.0, 2.5)

    #  The holes, from the ground: the trench behind the frame, then
    #  from before it the bottom's two and the trench before it
    stand(2.0, 0.0, -2.5)
    for x in range(4):
      dig(x, -1, -1)
    stand(*front)
    for x in range(4):
      dig(x, -1, 1)
    dig(1, -1, 0)
    dig(2, -1, 0)
    #  the bottom, cast in the trench: the water poured into it lies in
    #  the bottom's holes too, and lava poured into them is obsidian
    water('up', 1, -2, 1)
    for x in (1, 2):
      fetch()
      stand(*front)
      lava('up', x, -2, 0)
    scoop(1, -1, 1)
    #  the pillar's lower two rows, on the bottom
    for y in (-1, 0):
      dirt('up', 1, y, 0)
      dirt('up', 2, y, 0)
    #  the step, and the platform where it stood, from behind
    stand(2.0, 0.0, 3.5)
    dirt('up', 0, -1, 2)
    for y in (-1, 0):
      dirt('up', 1, y, 2)
      dirt('up', 2, y, 2)
    #  Up on the platform: the pillar's top row, and the water on its
    #  left half. It runs off over the left side, and before and behind
    stand(*up1)
    dirt('up', 1, 1, 0)
    dirt('up', 2, 1, 0)
    water('up', 1, 2, 0)
    #  the left side: lava against the pillar's west face, into the fall
    for y in range(3):
      fetch()
      stand(*left)
      lava('west', 1, y, 0)
    #  the water moved to the right half, and the right side the same
    stand(*up1)
    scoop(1, 3, 0)
    water('up', 2, 2, 0)
    for y in range(3):
      fetch()
      stand(*right)
      lava('east', 2, y, 0)
    #  the top: lava beside the water, then into the water's own cell
    for x in (1, 2):
      fetch()
      stand(*up1)
      lava('up', x, 2, 0)
    #  the pillar dug out of the portal's inside, a half from each side
    for spot, x in ((left, 1), (right, 2)):
      stand(*spot)
      for y in (2, 1, 0):
        dig(x, y, 0)
    #  the trench before it filled again, from each of its ends, the
    #  far cell first
    stand(-0.5, 0.0, 1.5)
    dirt('up', 1, -2, 1)
    dirt('up', 0, -2, 1)
    stand(4.5, 0.0, 1.5)
    dirt('up', 2, -2, 1)
    dirt('up', 3, -2, 1)
    #  lit on the bottom's top, from before it, and walked into
    stand(2.0, 0.0, 1.5)
    click(CastDoes.LIGHT, 'up', 1, -1, 0)
    made.append(CastMove(CastDoes.ENTER, spot=self.inside))
    return tuple(made)
