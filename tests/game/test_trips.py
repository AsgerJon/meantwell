"""
Long trips in a real game (SPEC.md 21.11 M1, 21.12), on the practice
instance: the traveller on the real agent, by a player's inputs alone.
The scene is built by command, as a scenario's setup is: a wall wider
than a look ahead of the start, and a dead end behind it. Where the
agent's own walkTo stops, the traveller is to arrive. Each trip's legs,
looks and ticks are noted under its line in the report.

  unittas run tests.game.test_trips
  (through meantwell_watch.py: that line in meantwell-queue/request)
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from mcdex import MCBlocks

from meantwell.traveller import Traveller
from tests.game.counted import Counted
from unittas.errors import TesttimeError
from unittas.scenario import ScenarioTestCase
from unittas.values import Vec3

#  Places from the scene's origin, the block the run's start stands in.
#  A wall two high across z 10, from x -14 to 10: wider than a look (8)
#  from the start's line, its nearer end 11 columns to the side
WALL_Z, WALL_X = 10, range(-14, 11)
BEYOND_THE_WALL = (0, 0, 20)
#  A dead end behind the start, open towards it: its back across z -14
#  from x -10 to 10, its sides along x -10 and x 10 from z -13 to -6
BACK_Z, BACK_X = -14, range(-10, 11)
SIDES_X, SIDES_Z = (-10, 10), range(-13, -5)
BEYOND_THE_DEAD_END = (0, 0, -22)
FAR_ON_OPEN_GROUND = (30, 0, 0)


class TripTests(ScenarioTestCase):

  #  a trip is long by the clock too: a guard, never the verdict
  timeout_seconds = 300

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    #  the setup is by command, not the agent
    columns = [(x, WALL_Z) for x in WALL_X]
    columns += [(x, BACK_Z) for x in BACK_X]
    columns += [(x, z) for x in SIDES_X for z in SIDES_Z]
    for x, z in columns:
      for up in (0, 1):
        cls.scene.place(MCBlocks.Stone, at=(x, up, z))

  def place(self, offset: tuple) -> Vec3:
    """The floor's middle of the place 'offset' from the origin."""
    return self.scene.at(offset).center()

  def travelled(self, goal: Vec3) -> None:
    """The traveller's trip to the goal, noted; a FAIL if it ends short."""
    start = self.agent.perceive().pos
    counted = Counted(self.agent)
    seen = Traveller(counted).travel(goal)
    short = math.hypot(goal.x - seen.pos.x, goal.z - seen.pos.z)
    infoSpec = """travelled: %.1f blocks straight, in %d legs (%d not
    completed) and %d looks, %d ticks; %.2f short"""
    straight = math.hypot(goal.x - start.x, goal.z - start.z)
    self.scene.note(' '.join((infoSpec % (
      straight, counted.legs, counted.failed, counted.looks, counted.ticks,
      short)).split()))
    self.assertLessEqual(short, 0.25)

  def stopped(self, goal: Vec3) -> None:
    """The agent's own walkTo to the goal: it is to stop short, noted."""
    with self.assertRaises(TesttimeError) as raised:
      self.agent.walkTo(goal)
    self.scene.note('walkTo alone: %s' % (raised.exception,))

  def test_1_far_on_open_ground(self) -> None:
    self.travelled(self.place(FAR_ON_OPEN_GROUND))

  def test_2_the_wall_stops_walkTo_alone(self) -> None:
    self.stopped(self.place(BEYOND_THE_WALL))

  def test_3_round_a_wall_wider_than_a_look(self) -> None:
    self.travelled(self.place(BEYOND_THE_WALL))

  def test_4_the_dead_end_stops_walkTo_alone(self) -> None:
    self.stopped(self.place(BEYOND_THE_DEAD_END))

  def test_5_out_of_a_dead_end(self) -> None:
    self.travelled(self.place(BEYOND_THE_DEAD_END))
