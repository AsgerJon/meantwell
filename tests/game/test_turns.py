"""
How a turn by the mouse goes in a real game, answer by answer (SPEC.md
21.24 K1), on the practice instance: the robot stands and turns a
quarter by the mouse as a walk has it and by a quick one, and each rate
it asked is noted with the tick and the look it was answered with. This
page is here to find out: the hands' test found a turn taking two to
four times the ticks the stand-in gives it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from meantwell.mouse import Mouse
from tests.game.bearings import Bearings
from tests.game.quickmouse import QuickMouse
from unittas.scenario import ScenarioTestCase


class TurnsTests(ScenarioTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 120
  world = {'type': 'flat', 'game_mode': 'survival', 'cheats': True,
           'structures': False}

  def turned(self, mouse: type, by: float) -> None:
    """A turn of 'by' degrees with a mouse of the class 'mouse', each
    answer noted."""
    body = Bearings(self.game)
    hand = mouse(body)
    first = self.agent.perceive()
    hand.look(first.look.yaw, 30.0)
    start = self.agent.perceive()
    wanted = (start.look.yaw + by + 180.0) % 360.0 - 180.0
    del body.kept[:], body.rates[:]
    hand.look(wanted, 30.0)
    end = self.agent.perceive()
    self.scene.note('%s, %.0f degrees: %d ticks, %d rates; from %.3f to '
                    '%.3f, wanted %.3f' % (
                      mouse.__name__, by, end.tick - start.tick - 1,
                      len(body.rates), start.look.yaw, end.look.yaw,
                      wanted))
    for bearing, rate in zip(body.kept, body.rates):
      self.scene.note('  tick %d: asked %7.3f, answered looking %8.3f' % (
        bearing.tick - start.tick, rate[0], bearing.look.yaw))

  def test_1_a_quarter_by_the_mouse(self) -> None:
    self.turned(Mouse, 90.0)

  def test_2_a_quarter_by_a_quick_mouse(self) -> None:
    self.turned(QuickMouse, 90.0)

  def test_3_forty_degrees_by_each(self) -> None:
    self.turned(Mouse, 40.0)
    self.turned(QuickMouse, -40.0)

  def test_4_turns_with_a_press_of_use_between(self) -> None:
    #  the hands' test took three times the ticks its turns account for:
    #  each look and each press timed here, by a perception before and
    #  after it (a tick each, taken off)
    hand = QuickMouse(self.game)
    first = self.agent.perceive()
    aims = [((first.look.yaw + by + 180.0) % 360.0 - 180.0, 35.0)
            for by in (-22.0, 22.0)]
    hand.look(*aims[0])
    for use in range(6):
      before = self.agent.perceive().tick
      hand.look(*aims[(use + 1) // 2 % 2])
      between = self.agent.perceive().tick
      self.game.tap('key.use')
      after = self.agent.perceive().tick
      self.scene.note('use %d: its look %d ticks, its press %d ticks' % (
        use, between - before - 1, after - between - 1))

  def test_5_the_same_with_no_perception_between(self) -> None:
    #  the hands' test without its perceptions took 197 ticks where
    #  with them it took 76: here each turn's rates are counted and the
    #  ticks from one turn's last answer to the next's, with nothing
    #  asked between a look and a press
    body = Bearings(self.game)
    hand = QuickMouse(body)
    first = self.agent.perceive()
    aims = [((first.look.yaw + by + 180.0) % 360.0 - 180.0, 35.0)
            for by in (-22.0, 22.0)]
    hand.look(*aims[0])
    start = self.agent.perceive().tick
    last, rates = start, len(body.rates)
    for use in range(10):
      hand.look(*aims[(use + 1) // 2 % 2])
      if len(body.rates) > rates:
        ends = body.kept[-1].tick
        self.scene.note(
          'use %d: a turn of %d rates, their answers from tick %d to %d; '
          '%d ticks since the turn before ended' % (
            use, len(body.rates) - rates, body.kept[rates].tick - start,
            ends - start, ends - last))
        last, rates = ends, len(body.rates)
      self.game.tap('key.use')
    self.scene.note('in all %d ticks' % (
      self.agent.perceive().tick - start - 1,))
