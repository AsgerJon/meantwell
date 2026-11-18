"""
The traveller on long trips (SPEC.md 21.11, M1), without a game, in the
grid agent's world of whole blocks (gridworld.py), whose walkTo finds
its way on one look as the agent's does. Where that walkTo alone stops
(a wall wider than a look, a dead end), the traveller arrives: it
remembers the ground it was shown, goes to the edge of it to look
further, and never goes back into a dead end it has seen. It walks in
legs within one look, by the agent's own perceive and walkTo and nothing
else. No way in all it has seen, its tick budget spent, or a leg the
agent can't complete three times in a row is a TesttimeError.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from gridworld import (GROUND, GridAgent, arena, lake, stoodIn,
                       stoodInWater, wall)
from meantwell.atlas import Atlas
from meantwell.traveller import Traveller
from stoppedagent import StoppedAgent
from unittas.errors import TesttimeError
from unittas.values import BlockPos, Vec3


def _far(a: Vec3, b: Vec3) -> float:
  return math.hypot(a.x - b.x, a.z - b.z)


class TravellerTests(unittest.TestCase):

  def test_a_place_far_off_on_open_ground(self) -> None:
    start, goal = Vec3(6.5, GROUND, 2.5), Vec3(6.5, GROUND, 36.5)
    agent = GridAgent(arena(12, 40), start)
    seen = Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    self.assertEqual(goal, seen.pos)
    #  in legs within one look, only the last stopping precisely
    self.assertGreaterEqual(len(agent.legs), 5)
    for stood, (place, within) in zip(agent.stood, agent.legs):
      self.assertLessEqual(_far(stood, place), Traveller.LEG + 1e-6)
    self.assertEqual([1.0] * (len(agent.legs) - 1) + [0.25],
                     [within for _, within in agent.legs])

  def test_a_place_near_is_the_agents_own_walk(self) -> None:
    goal = Vec3(8.5, GROUND, 5.5)
    agent = GridAgent(arena(12, 12), Vec3(6.5, GROUND, 2.5))
    Traveller(agent).travel(goal, within=0.1)
    self.assertEqual([(goal, 0.1)], agent.legs)

  def test_a_wall_wider_than_a_look(self) -> None:
    #  across the arena but for a gap far to one side
    world = arena(40, 30) | wall(0, 14, 33, 14)
    start, goal = Vec3(4.5, GROUND, 4.5), Vec3(4.5, GROUND, 24.5)
    alone = GridAgent(world, start)
    with self.assertRaises(TesttimeError) as stopped:
      alone.walkTo(goal)
    self.assertIn('further than 12 looks', str(stopped.exception))
    agent = GridAgent(world, start)
    Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    self.assertGreater(stoodIn(agent, 30, 0, 39, 29), 0,
                       'it went to the far side, where the gap is')

  def test_a_dead_end_is_left_and_never_gone_back_into(self) -> None:
    #  a cup open towards the start, the goal behind it
    world = (arena(30, 40) | wall(8, 20, 22, 20) | wall(8, 10, 8, 20) |
             wall(22, 10, 22, 20))
    start, goal = Vec3(15.5, GROUND, 3.5), Vec3(15.5, GROUND, 34.5)
    with self.assertRaises(TesttimeError):
      GridAgent(world, start).walkTo(goal)
    agent = GridAgent(world, start)
    Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    inside = [9 <= math.floor(pos.x) <= 21 and 11 <= math.floor(pos.z) <= 19
              for pos in agent.stood]
    self.assertIn(True, inside, 'it went in: the straight way looked best')
    last = len(inside) - 1 - inside[::-1].index(True)
    first = inside.index(True)
    self.assertTrue(all(inside[first:last + 1]),
                    'once out of the dead end it never went back in')

  def test_no_way_in_all_it_has_seen(self) -> None:
    #  the goal walled in
    world = (arena(20, 20) | wall(8, 13, 12, 13) | wall(8, 17, 12, 17) |
             wall(8, 13, 8, 17) | wall(12, 13, 12, 17))
    agent = GridAgent(world, Vec3(10.5, GROUND, 2.5))
    traveller = Traveller(agent)
    with self.assertRaises(TesttimeError) as stopped:
      traveller.travel(Vec3(10.5, GROUND, 15.5))
    error = stopped.exception
    self.assertEqual('travel', error.step)
    self.assertIn('no way to (10.50, 4.00, 15.50)', str(error))
    self.assertIn('in all it has seen', str(error))
    #  it looked everywhere it could get to before it said so
    self.assertTrue(all(traveller.atlas.knows(x, z) for x in range(20)
                        for z in range(20)))

  def test_a_lake_wider_than_a_look_is_gone_round(self) -> None:
    #  found in the game (SPEC.md 21.14): the edge of what it had seen
    #  lay in water, it went there, and the agent walked in and sank
    world, water = lake(arena(40, 34), 6, 12, 33, 20)
    start, goal = Vec3(20.5, GROUND, 4.5), Vec3(20.5, GROUND, 28.5)
    agent = GridAgent(world, start, water)
    Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    self.assertFalse(agent.sunk)
    self.assertEqual(0, stoodInWater(agent), 'no leg ends in water')

  def test_water_it_sees_across_is_swum(self) -> None:
    #  a river four wide from side to side: no way round it
    world, water = lake(arena(20, 30), 0, 12, 19, 15)
    start, goal = Vec3(10.5, GROUND, 4.5), Vec3(10.5, GROUND, 24.5)
    agent = GridAgent(world, start, water)
    Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    self.assertFalse(agent.sunk)
    self.assertEqual(0, stoodInWater(agent))

  def test_water_too_wide_to_see_across_is_no_way(self) -> None:
    #  water ten wide from side to side, the goal beyond it
    world, water = lake(arena(20, 34), 0, 12, 19, 21)
    agent = GridAgent(world, Vec3(10.5, GROUND, 4.5), water)
    with self.assertRaises(TesttimeError) as stopped:
      Traveller(agent).travel(Vec3(10.5, GROUND, 28.5))
    self.assertIn('no way to (10.50, 4.00, 28.50)', str(stopped.exception))
    self.assertFalse(agent.sunk, 'it stays out of water it can\'t cross')
    self.assertEqual(0, stoodInWater(agent))

  def test_the_tick_budget_spent(self) -> None:
    agent = GridAgent(arena(12, 40), Vec3(6.5, GROUND, 2.5))
    with self.assertRaises(TesttimeError) as stopped:
      Traveller(agent).travel(Vec3(6.5, GROUND, 36.5), ticks=40)
    self.assertEqual('travel', stopped.exception.step)
    self.assertIn('the tick budget (40) is spent', str(stopped.exception))
    self.assertLess(agent.pos.z, 36.0)

  def test_the_world_changes_on_the_way(self) -> None:
    #  a wall with two gaps; the nearer is shut as the agent sets out
    world = arena(26, 30) | wall(0, 14, 7, 14) | wall(10, 14, 20, 14)
    start, goal = Vec3(9.5, GROUND, 3.5), Vec3(9.5, GROUND, 26.5)
    agent = GridAgent(world, start)

    def shut(grid: GridAgent) -> None:
      if len(grid.legs) == 1:
        grid.solid |= wall(8, 14, 9, 14)

    agent.onLeg = shut
    Traveller(agent).travel(goal)
    self.assertEqual(goal, agent.pos)
    self.assertIn((8, 4, 14), agent.solid)
    self.assertGreater(stoodIn(agent, 19, 0, 25, 29), 0,
                       'it went to the gap left open')

  def test_a_leg_the_agent_cant_complete_three_times(self) -> None:
    stopped = StoppedAgent(GridAgent(arena(12, 40),
                                     Vec3(6.5, GROUND, 2.5)))
    with self.assertRaises(TesttimeError) as raised:
      Traveller(stopped).travel(Vec3(6.5, GROUND, 36.5))
    error = raised.exception
    self.assertEqual('travel', error.step)
    self.assertIn('stopped 3 times in a row', str(error))
    self.assertIn('blocked by something it can\'t see', str(error))
    self.assertIsInstance(error.__cause__, TesttimeError)
    self.assertEqual(3, stopped.asked)

  def test_a_blockpos_is_its_floors_middle(self) -> None:
    agent = GridAgent(arena(12, 12), Vec3(6.5, GROUND, 2.5))
    Traveller(agent).travel(BlockPos(8, 4, 5))
    self.assertEqual(Vec3(8.5, GROUND, 5.5), agent.pos)

  def test_made_wrong_it_is_refused(self) -> None:
    agent = GridAgent(arena(12, 12), Vec3(6.5, GROUND, 2.5))
    traveller = Traveller(agent)
    with self.assertRaises(TypeError):
      traveller.travel('over there')
    with self.assertRaises(ValueError):
      traveller.travel(Vec3(8.5, GROUND, 5.5), ticks=0)
    with self.assertRaises(ValueError):
      traveller.travel(Vec3(8.5, GROUND, 5.5), within=0.01)
    self.assertEqual([], agent.legs)

  def test_it_remembers_from_one_trip_to_the_next(self) -> None:
    atlas = Atlas()
    agent = GridAgent(arena(12, 40), Vec3(6.5, GROUND, 2.5))
    traveller = Traveller(agent, atlas)
    self.assertIs(atlas, traveller.atlas)
    self.assertIs(agent, traveller.agent)
    traveller.travel(Vec3(6.5, GROUND, 36.5))
    looks, legs = agent.looks, len(agent.legs)
    #  back again: the way is remembered whole, so no edge is gone to
    traveller.travel(Vec3(6.5, GROUND, 2.5))
    self.assertEqual(Vec3(6.5, GROUND, 2.5), agent.pos)
    self.assertLessEqual(len(agent.legs) - legs, legs)
    self.assertGreater(agent.looks, looks)


if __name__ == '__main__':
  unittest.main()
