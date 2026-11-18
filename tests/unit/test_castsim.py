"""
The world of blocks a cast's plan is played in (castsim.py), held to
what the practice game showed of water (SPEC.md 21.20, 21.21): a
stand-in the game hasn't confirmed teaches the plan the stand-in. Its
first cast in the game stopped with water where the plan had none; the
world here is to put it in those same cells.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from castsim import CastSim
from unittas.values import Vec3

GROUND = -1


class CastSimTests(unittest.TestCase):

  def world(self, **blocks) -> CastSim:
    """A bare world, the ground's top blocks at y -1, with the blocks
    given: dirt=..., obsidian=..., dug=... (cells)."""
    made = CastSim(GROUND, (), Vec3(0.5, 0.0, 9.5), (), (),
                   Vec3(0.5, 0.0, 9.5))
    for kind in ('dirt', 'obsidian'):
      for cell in blocks.get(kind, ()):
        made.blocks[cell] = kind
    made.dug |= set(blocks.get('dug', ()))
    return made

  def poured(self, world: CastSim, cell: tuple) -> CastSim:
    world.sources.add(cell)
    world.water[cell] = 8
    world.flow()
    return world

  def test_the_first_casts_water_is_where_the_game_had_it(self) -> None:
    #  2026-11-18 19:55, in the cast's own places: the left post four
    #  high at (-1, y, 1), the drain under (0, 0, 1), the bottom's two
    #  and the left side's first block obsidian, the platform and its
    #  step, the water poured against the post's top. By command the
    #  game had water in the left side's two upper cells and in two of
    #  the frame's inside, (1, 0) and (1, 1); none in the other four.
    world = self.world(
      dirt=[(-1, y, 1) for y in range(4)] + [(4, 0, 1), (4, 1, 1)] + [
        (1, 0, 3), (1, 0, 2), (2, 0, 2), (1, 1, 2), (2, 1, 2)],
      obsidian=[(1, -1, 0), (2, -1, 0), (0, 0, 0)],
      dug=[(0, -1, 1), (3, -1, 1)])
    self.poured(world, (0, 3, 1))
    for cell in ((0, 1, 0), (0, 2, 0), (1, 0, 0), (1, 1, 0)):
      self.assertIn(cell, world.water, cell)
    for cell in ((1, 2, 0), (2, 0, 0), (2, 1, 0), (2, 2, 0)):
      self.assertNotIn(cell, world.water, cell)

  def test_on_level_ground_it_runs_seven_blocks_every_way(self) -> None:
    world = self.poured(self.world(), (0, 0, 0))
    self.assertEqual(8, world.water[(0, 0, 0)])
    self.assertEqual(1, world.water[(7, 0, 0)])
    self.assertEqual(1, world.water[(3, 0, -4)])
    self.assertNotIn((8, 0, 0), world.water)
    self.assertNotIn((4, 0, 4), world.water)

  def test_in_a_hole_it_lies_still(self) -> None:
    world = self.poured(self.world(dug=[(0, -1, 0)]), (0, -1, 0))
    self.assertEqual({(0, -1, 0): 8}, world.water)

  def test_a_hole_beside_it_takes_it_all(self) -> None:
    #  Asger, of the block he digs: "critical to keep the water from
    #  just flowing"
    world = self.poured(self.world(dug=[(1, -1, 0)]), (0, 0, 0))
    self.assertEqual({(0, 0, 0), (1, 0, 0), (1, -1, 0)}, set(world.water))

  def test_a_hole_within_four_blocks_draws_it(self) -> None:
    world = self.poured(self.world(dug=[(3, -1, 0)]), (0, 0, 0))
    self.assertEqual({(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0),
                      (3, -1, 0)}, set(world.water))

  def test_a_source_on_a_pillar_falls_down_all_four_sides(self) -> None:
    world = self.poured(self.world(dirt=[(0, 0, 0), (0, 1, 0)]), (0, 2, 0))
    for side in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      for y in (2, 1, 0):
        self.assertIn((side[0], y, side[1]), world.water)

  def test_a_source_in_the_air_runs_to_its_sides_too(self) -> None:
    #  the belief the first cast was planned on: that it only falls
    world = self.poured(self.world(), (0, 3, 0))
    self.assertIn((0, 0, 0), world.water)
    for side in ((1, 3, 0), (-1, 3, 0), (0, 3, 1), (0, 3, -1)):
      self.assertIn(side, world.water)

  def test_water_that_only_runs_falls_and_no_more(self) -> None:
    world = self.poured(self.world(dirt=[(0, 2, 0)]), (0, 3, 0))
    #  it ran off the block to (1, 3, 0) and fell: nothing beside its fall
    self.assertIn((1, 1, 0), world.water)
    self.assertNotIn((2, 1, 0), world.water)
    self.assertNotIn((2, 3, 0), world.water)

  def test_its_source_gone_it_runs_dry(self) -> None:
    world = self.poured(self.world(dirt=[(0, 0, 0), (0, 1, 0)]), (0, 2, 0))
    world.sources.discard((0, 2, 0))
    del world.water[(0, 2, 0)]
    world.flow()
    self.assertEqual({}, world.water)

  def test_lava_it_runs_beside_or_over_is_obsidian(self) -> None:
    world = self.world(dug=[(2, -1, 0)])
    world.blocks[(2, -1, 0)] = 'lava'
    world.blocks[(0, 0, 2)] = 'lava'
    world.lake = {(2, -1, 0)}
    self.poured(world, (0, 0, 0))
    self.assertEqual('obsidian', world.kind((2, -1, 0)), 'under it')
    self.assertEqual('obsidian', world.kind((0, 0, 2)), 'beside it')
    self.assertEqual({(2, -1, 0)}, world.crusted)


if __name__ == '__main__':
  unittest.main()
