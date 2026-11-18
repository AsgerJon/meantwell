"""
The plan of a portal cast (SPEC.md 21.21; portalcast.py), without a
game: its moves played in a world of blocks that holds them to what the
practice game measured of buckets and to what a player can click from
where it stands (castsim.py). Played through, the frame's ten blocks are
obsidian, the portal is lit and stood in, the water never ran and the
lava never did, on ten bucketfuls of lava and a few blocks of dirt. And
the world it is played in does catch a plan that is wrong.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from castsim import CastSim
from meantwell.castdoes import CastDoes
from meantwell.castmove import CastMove
from meantwell.portalcast import PortalCast
from unittas.values import BlockPos

ORIGIN = BlockPos(10, 64, 20)


class PortalCastTests(unittest.TestCase):

  def world(self, cast: PortalCast, **more) -> CastSim:
    return CastSim(cast.origin.y - 1, cast.lake, cast.spot(2.0, 0.0, 4.5),
                   cast.frame, cast.interior, cast.shore, **more)

  def played(self, moves: tuple = None, **more) -> CastSim:
    cast = PortalCast(ORIGIN)
    world = self.world(cast, **more)
    world.play(cast.moves if moves is None else moves)
    return world

  def test_the_frame_is_a_portals(self) -> None:
    cast = PortalCast(ORIGIN)
    frame = {(cell.x - 10, cell.y - 64, cell.z - 20) for cell in cast.frame}
    self.assertEqual({(1, -1, 0), (2, -1, 0), (0, 0, 0), (0, 1, 0),
                      (0, 2, 0), (3, 0, 0), (3, 1, 0), (3, 2, 0),
                      (1, 3, 0), (2, 3, 0)}, frame)
    inside = {(cell.x - 10, cell.y - 64, cell.z - 20)
              for cell in cast.interior}
    self.assertEqual({(x, y, 0) for x in (1, 2) for y in (0, 1, 2)}, inside)

  def test_played_through_the_portal_stands_lit(self) -> None:
    world = self.played()
    self.assertEqual([], world.faults)
    for cell in world.frame:
      self.assertEqual('obsidian', world.kind(cell), cell)
    self.assertTrue(world.lit)
    self.assertTrue(world.entered)

  def test_ten_bucketfuls_of_lava_and_little_dirt(self) -> None:
    world = self.played()
    self.assertEqual(10, world.fetches)
    self.assertGreaterEqual(world.dirt, 64 - 20)
    self.assertEqual('nothing', world.bucket,
                     'its water went into the last block')
    self.assertEqual({}, world.water, 'and none is left running')

  def test_the_water_runs_but_not_off(self) -> None:
    #  it runs from the pillar's top, and the trenches take it: on the
    #  ground it is never further than a block from the frame, never
    #  where the robot stands or walks, never at the lake
    world = self.played()
    ground = {(x - 10, z - 20) for x, y, z in world.wetted if y == 64}
    self.assertTrue(ground, 'it did run')
    self.assertLessEqual(ground, {(x, z) for x in range(-1, 5)
                                  for z in (-1, 0, 1)})
    high = {y - 64 for x, y, z in world.wetted}
    self.assertEqual(3, max(high), 'from the pillar\'s top')
    self.assertEqual(set(), world.crusted)
    lava = [cell for cell in world.lake if world.kind(cell) == 'lava']
    self.assertEqual(len(world.lake) - 10, len(lava))

  def test_each_side_is_cast_in_the_fall(self) -> None:
    #  as a speedrunner does it: lava against the pillar, into the water
    #  that falls there, and it is obsidian as it is poured
    cast = PortalCast(ORIGIN)
    world = self.world(cast)
    sides = [cast.at(x, y, 0) for x in (0, 3) for y in (0, 1, 2)]
    for move in cast.moves:
      into = None
      if move.does is CastDoes.POUR_LAVA and move.face in ('west', 'east'):
        into = move.pos.offset(-1 if move.face == 'west' else 1, 0, 0)
        self.assertIn((into.x, into.y, into.z), world.water, str(move))
      self.assertEqual([], world.play((move,)))
      if into is not None:
        self.assertIn(into, sides)
        self.assertEqual('obsidian', world.kind((into.x, into.y, into.z)))

  def test_it_is_the_same_plan_wherever_it_is(self) -> None:
    here, there = PortalCast(ORIGIN), PortalCast(BlockPos(-40, 70, 3))
    self.assertEqual(len(here.moves), len(there.moves))
    for one, other in zip(here.moves, there.moves):
      self.assertIs(one.does, other.does)
      self.assertEqual(one.face, other.face)
      if one.pos is not None:
        self.assertEqual((one.pos.x - 10, one.pos.y - 64, one.pos.z - 20),
                         (other.pos.x + 40, other.pos.y - 70,
                          other.pos.z - 3))

  def test_each_move_says_what_it_is(self) -> None:
    said = [str(move) for move in PortalCast(ORIGIN).moves]
    self.assertIn('dig the block at (11, 63, 20)', said)
    self.assertIn('fetch lava from the lake', said)
    self.assertIn(
      'pour water on the up face of the block at (11, 62, 21)', said)
    self.assertIn('scoop the water at (11, 63, 21)', said)
    self.assertIn('stand at (11.50, 66.00, 22.50)', said)
    self.assertIn(
      'pour lava on the west face of the block at (11, 65, 20)', said)
    self.assertIn('light the up face of the block at (11, 63, 20)', said)
    self.assertEqual('stand in the portal at (12.00, 64.00, 20.50)',
                     said[-1])

  def test_a_move_is_refused_when_made_wrong(self) -> None:
    with self.assertRaises(TypeError):
      CastMove(CastDoes.DIG)
    with self.assertRaises(TypeError):
      CastMove(CastDoes.DIRT, BlockPos(1, 2, 3))
    with self.assertRaises(ValueError):
      CastMove(CastDoes.DIRT, BlockPos(1, 2, 3), 'sideways')
    with self.assertRaises(TypeError):
      CastMove(CastDoes.STAND, BlockPos(1, 2, 3))
    with self.assertRaises(TypeError):
      CastMove(CastDoes.FETCH_LAVA, BlockPos(1, 2, 3))

  # ------------------------------------------ the world catches a wrong plan

  def without(self, does: CastDoes, *which: int) -> tuple:
    """The plan without those of its moves of that kind (the first is
    1)."""
    moves, met = [], 0
    for move in PortalCast(ORIGIN).moves:
      if move.does is does:
        met += 1
        if met in which:
          continue
      moves.append(move)
    return tuple(moves)

  def test_too_little_dug_and_the_water_runs_off(self) -> None:
    #  Asger: "I dig up a seemingly inconsequential block behind the
    #  portal. That one is critical to keep the water from just flowing"
    #  Here: no trench behind, and the one before it only two long. What
    #  falls behind the pillar then has no way down within four blocks
    #  and it runs off over the ground, as far as the lake
    world = self.played(self.without(CastDoes.DIG, 1, 2, 3, 4, 5, 8))
    self.assertTrue(world.faults)
    self.assertTrue('runs off' in world.faults[0] or
                    'reached the lake' in world.faults[0], world.faults[0])
    self.assertNotEqual('obsidian', world.kind(world.frame[-1]))

  def test_the_trench_behind_alone_is_more_than_it_needs(self) -> None:
    #  without it the water behind still finds the trench before the
    #  frame, round the frame's foot, four blocks off: the most it can
    #  find. The plan digs both, and doesn't lean on that
    world = self.played(self.without(CastDoes.DIG, 1, 2, 3, 4))
    self.assertEqual([], world.faults)

  def test_lava_with_no_water_by_it_runs(self) -> None:
    #  the third water poured is the one on the pillar's top
    world = self.played(self.without(CastDoes.POUR_WATER, 2))
    self.assertTrue(world.faults)
    self.assertIn('lava', world.faults[0])

  def test_a_click_from_the_wrong_place_is_caught(self) -> None:
    cast = PortalCast(ORIGIN)
    moves = [move for move in cast.moves
             if not (move.does is CastDoes.STAND and move.spot.y > 64.5)]
    world = self.played(tuple(moves))
    self.assertTrue(world.faults, 'never up on its platform')

  def test_too_little_dirt_is_caught(self) -> None:
    world = self.played(dirt=5)
    self.assertTrue(world.faults)
    self.assertIn('no dirt left', world.faults[0])


if __name__ == '__main__':
  unittest.main()
