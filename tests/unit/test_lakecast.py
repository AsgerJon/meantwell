"""
The lava lake's portal, as a speedrunner's beginner casts it (SPEC.md
21.24; lakecast.py), without a game. The moves it needs that the first
cast had not: lava scooped where it stands, a block put under its own
feet, a lean over the edge of what it stands on. And the plan itself,
played in a world of blocks whose water runs by the game's rule
(castsim.py), in a lake one deep with a floor about it, as the MCSR
map's level is: it ends in a lit portal with the robot in it, and the
lake's lava turned only where the cast means it to.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from castsim import CastSim
from meantwell import lakecast
from meantwell.castdoes import CastDoes
from meantwell.castmove import CastMove
from meantwell.lakecast import LakeCast
from unittas.values import BlockPos, Vec3

#  Where the tests' cast is: its edge row's cell at x 0, the ground under
#  the shore at y 63
ORIGIN = BlockPos(10, 64, 20)


class LakeCastTests(unittest.TestCase):

  def world(self, cast: LakeCast) -> CastSim:
    """A lake one deep with a floor about it, as the cast is for."""
    return CastSim(ORIGIN.y - 1, cast.lake, cast.start, cast.frame,
                   cast.interior, cast.start, dirt=16, crusts=cast.crusts,
                   wades=True)

  def without(self, cast: LakeCast, does: CastDoes, *cells: tuple) -> list:
    """The faults of the cast played without its moves of that kind on
    those of its own places."""
    left = tuple(cast.at(*cell) for cell in cells)
    world = self.world(cast)
    return world.play(tuple(move for move in cast.moves if not (
      move.does is does and move.pos in left)))

  def test_the_cast_is_sound_and_ends_in_a_lit_portal(self) -> None:
    cast = LakeCast(ORIGIN)
    world = self.world(cast)
    self.assertEqual([], world.play(cast.moves))
    self.assertEqual(44, world.played)
    self.assertTrue(world.lit)
    self.assertTrue(world.entered)
    for cell in cast.frame:
      self.assertEqual('obsidian', world.kind(world._key(cell)), cell)
    self.assertEqual({}, world.water, 'no water left')
    self.assertEqual('water', world.bucket, 'the water in its bucket again')

  def test_it_turns_the_lakes_lava_only_where_it_means_to(self) -> None:
    cast = LakeCast(ORIGIN)
    world = self.world(cast)
    world.play(cast.moves)
    self.assertEqual({world._key(cell) for cell in cast.crusts},
                     world.crusted)

  def test_it_puts_down_seven_blocks_of_its_sixteen(self) -> None:
    cast = LakeCast(ORIGIN)
    world = self.world(cast)
    world.play(cast.moves)
    self.assertEqual(7, cast.blocks)
    #  the opening's block is dug out again, not picked up here
    self.assertEqual(16 - 7, world.dirt)

  def test_it_never_walks_to_fetch(self) -> None:
    cast = LakeCast(ORIGIN)
    does = [move.does for move in cast.moves]
    self.assertNotIn(CastDoes.FETCH_LAVA, does)
    self.assertEqual(8, does.count(CastDoes.SCOOP_LAVA))
    self.assertLessEqual(does.count(CastDoes.STAND), 7)

  def test_the_two_blocks_keep_the_water_off_the_lake(self) -> None:
    #  Asger: "they make it so that the water can flow like this
    #  without ... messing up the lava"
    cast = LakeCast(ORIGIN)
    faults = self.without(cast, CastDoes.DIRT, (2, -1, -1))
    self.assertTrue(any('the water reached the lake' in fault
                        for fault in faults), faults)
    #  and without the second the left side's upper block gets no water
    faults = self.without(cast, CastDoes.DIRT, (3, -1, -1))
    self.assertTrue(any('no water came to it' in fault
                        for fault in faults), faults)

  def test_the_arm_is_what_the_top_is_poured_against(self) -> None:
    cast = LakeCast(ORIGIN)
    faults = self.without(cast, CastDoes.DIRT, (5, 2, -1))
    self.assertEqual(1, len(faults))
    self.assertIn('nothing to click', faults[0])

  def test_without_the_bottom_made_there_is_no_portal(self) -> None:
    #  a lake one deep: the two blocks under the water are dug out and
    #  lava put in their place
    cast = LakeCast(ORIGIN)
    faults = self.without(cast, CastDoes.POUR_LAVA, (3, -3, 0), (4, -3, 0))
    self.assertTrue(faults)

  def test_its_places_are_its_origins(self) -> None:
    cast = LakeCast(ORIGIN)
    self.assertEqual(BlockPos(12, 63, 20), cast.frame[2])
    self.assertEqual(10, len(cast.frame))
    self.assertEqual(6, len(cast.interior))
    self.assertEqual(Vec3(13.5, 63.0, 20.5), cast.inside)
    self.assertEqual(121, len(cast.lake))
    self.assertEqual(lakecast.HOLE, (3, -1, -2))

  def test_the_new_moves_are_said_as_a_person_says_them(self) -> None:
    self.assertEqual('scoop the lava at (4, 63, 20)', str(CastMove(
      CastDoes.SCOOP_LAVA, BlockPos(4, 63, 20))))
    self.assertEqual('put a block under its feet', str(CastMove(
      CastDoes.PILLAR)))
    self.assertEqual('lean over the south edge of what it stands on',
                     str(CastMove(CastDoes.LEAN, face='south')))

  def test_each_is_refused_a_part_it_cant_have(self) -> None:
    with self.assertRaises(TypeError):
      CastMove(CastDoes.SCOOP_LAVA)
    with self.assertRaises(TypeError):
      CastMove(CastDoes.PILLAR, BlockPos(1, 2, 3))
    with self.assertRaises(TypeError):
      CastMove(CastDoes.LEAN)
    with self.assertRaises(TypeError):
      CastMove(CastDoes.LEAN, BlockPos(1, 2, 3), 'south')
    with self.assertRaises(ValueError):
      CastMove(CastDoes.LEAN, face='up')
    with self.assertRaises(TypeError):
      CastMove(CastDoes.LEAN, face='south', spot=Vec3(0.5, 0.0, 0.5))


if __name__ == '__main__':
  unittest.main()
