"""
The atlas, what the agent remembers of the ground (SPEC.md 21.11, M1),
without a game, on perceptions made by hand and by the grid agent
(gridworld.py): a look's blocks are remembered, and the rest of its box
is known to be air; a later look replaces an earlier one's, cell by
cell; and what it remembers around a place is one perception, on which
unittas's own Terrain finds a way that no single look shows.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from gridworld import FLOOR, GROUND, GridAgent, arena
from meantwell.atlas import Atlas
from unittas.perception import Perception
from unittas.terrain import Terrain
from unittas.values import Vec3

START = Vec3(4.5, GROUND, 4.5)
LOOK = (3, 1, 1)


class AtlasTests(unittest.TestCase):

  def setUp(self) -> None:
    self.agent = GridAgent(arena(9, 30) | {(4, FLOOR + 1, 6)}, START)
    self.atlas = Atlas()

  def look(self, at: Vec3 = None, look: tuple = LOOK) -> Perception:
    """The grid agent's look from 'at', noted in the atlas."""
    if at is not None:
      self.agent.pos = at
    seen = self.agent.perceive(*look)
    self.atlas.note(seen, *look)
    return seen

  def test_nothing_is_known_at_first(self) -> None:
    self.assertEqual(0, self.atlas.looks)
    self.assertEqual(0, self.atlas.columns)
    self.assertFalse(self.atlas.knows(4, 4))
    self.assertIsNone(self.atlas.block(4, FLOOR, 4))

  def test_a_looks_blocks_are_remembered(self) -> None:
    seen = self.look()
    self.assertEqual(1, self.atlas.looks)
    self.assertEqual(7 * 7, self.atlas.columns)
    self.assertEqual('minecraft:stone', self.atlas.block(4, FLOOR, 4).id)
    self.assertEqual((4, FLOOR + 1, 6), tuple(
      self.atlas.block(4, FLOOR + 1, 6).pos))
    self.assertEqual(len(seen.blocks), len(self.atlas.ground(START,
                                                             3).blocks))

  def test_the_rest_of_its_box_is_known_to_be_air(self) -> None:
    self.look()
    #  the box: 3 columns around, from 1 under the feet's block to 1 over
    #  the head's
    self.assertTrue(self.atlas.known(4, FLOOR + 1, 4))
    self.assertIsNone(self.atlas.block(4, FLOOR + 1, 4))
    self.assertTrue(self.atlas.known(7, FLOOR + 3, 1))
    self.assertFalse(self.atlas.known(4, FLOOR + 4, 4), 'above the box')
    self.assertFalse(self.atlas.known(4, FLOOR - 1, 4), 'below the box')
    self.assertFalse(self.atlas.known(8, FLOOR + 1, 4), 'beside the box')
    self.assertTrue(self.atlas.knows(7, 7))
    self.assertFalse(self.atlas.knows(8, 4))

  def test_a_later_look_replaces_an_earlier_ones(self) -> None:
    self.look()
    self.agent.solid.discard((4, FLOOR + 1, 6))
    self.agent.solid.add((5, FLOOR + 1, 3))
    self.look()
    self.assertIsNone(self.atlas.block(4, FLOOR + 1, 6), 'broken since')
    self.assertTrue(self.atlas.known(4, FLOOR + 1, 6))
    self.assertIsNotNone(self.atlas.block(5, FLOOR + 1, 3), 'placed since')
    self.assertEqual(2, self.atlas.looks)
    self.assertEqual(7 * 7, self.atlas.columns)

  def test_what_a_later_look_doesnt_show_is_kept(self) -> None:
    self.look()
    self.agent.solid.discard((4, FLOOR + 1, 6))
    self.look(Vec3(4.5, GROUND, 14.5))
    self.assertIsNotNone(self.atlas.block(4, FLOOR + 1, 6),
                         'out of the later look: as it was remembered')
    self.assertEqual(2 * 7 * 7, self.atlas.columns)

  def test_two_looks_make_one_ground(self) -> None:
    far = Vec3(4.5, GROUND, 10.5)
    self.look()
    alone = Terrain(self.atlas.ground(START, 16), 16, 0, 0)
    self.assertEqual((None, True), alone.path(START, far),
                     'a column not seen is no way')
    self.look(Vec3(4.5, GROUND, 9.5))
    both = Terrain(self.atlas.ground(START, 16), 16, 0, 0)
    path, whole = both.path(START, far)
    self.assertTrue(whole)
    self.assertEqual(far, path[-1])
    #  around the block in the way, at (4, 6)
    self.assertFalse(any(int(point.x) == 4 and int(point.z) == 6
                         for point in path))

  def test_its_ground_is_what_is_around_the_place(self) -> None:
    self.look()
    self.look(Vec3(4.5, GROUND, 14.5))
    near = self.atlas.ground(START, 2)
    self.assertEqual(START, near.pos)
    self.assertTrue(all(abs(block.pos.x - 4) <= 2 and
                        abs(block.pos.z - 4) <= 2 for block in near.blocks))
    self.assertEqual(5 * 5 + 1, len(near.blocks))

  def test_the_edge_is_where_what_was_seen_ends(self) -> None:
    self.look()
    edges = self.atlas.edges(4, 4, 16)
    self.assertEqual(4 * 6, len(edges))
    self.assertIn((1, 4), edges)
    self.assertIn((7, 7), edges)
    self.assertNotIn((4, 4), edges)
    self.assertNotIn((2, 4), edges)
    #  only those around the place asked about
    self.assertEqual({(1, 3), (1, 4), (1, 5)},
                     set(self.atlas.edges(1, 4, 1)))

  def test_a_look_made_wrong_is_refused(self) -> None:
    seen = self.agent.perceive(*LOOK)
    for wrong in ((-1, 1, 1), (3, -1, 1), (3, 1, -1)):
      with self.subTest(wrong=wrong):
        with self.assertRaises(ValueError):
          self.atlas.note(seen, *wrong)
    with self.assertRaises(TypeError):
      self.atlas.note('a look', *LOOK)
    self.assertEqual(0, self.atlas.looks)


if __name__ == '__main__':
  unittest.main()
