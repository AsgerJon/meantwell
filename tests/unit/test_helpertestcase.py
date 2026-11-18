"""
HelperTestCase, meantwell's front for unitTAS's tests (SPEC.md 21.19
S3), without a game: a scenario's test case whose every test has a
helper of its own on the scenario's agent, saying to the scene's notes,
and 'play', which the helper must do. Here the agent only records
(recorder.py) and the scene only notes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import types
import unittest

from mcdex import MCBlocks, MCItems

from handle import Handle
from meantwell.helper import Helper
from meantwell.helpertestcase import HelperTestCase
from meantwell.verb import Verb
from recorder import Recorder
from unittas.container import Container
from unittas.errors import TesttimeError
from unittas.scenario import ScenarioTestCase
from unittas.values import BlockPos, Item

CHEST = BlockPos(0, 4, 6)
WOOL = Item('minecraft:wool', 1, 6)


class HelperTestCaseTests(unittest.TestCase):

  def case(self, **agent) -> HelperTestCase:
    """A test of such a case, set up on a recorder and a list of notes."""
    case = HelperTestCase('play')
    case.agent = Recorder(**agent)
    self.notes = []
    case.scene = types.SimpleNamespace(note=self.notes.append)
    case.setUp()
    return case

  def test_it_is_a_scenarios_test_case(self) -> None:
    self.assertTrue(issubclass(HelperTestCase, ScenarioTestCase))

  def test_each_test_has_a_helper_of_its_own_on_the_agent(self) -> None:
    case = self.case()
    self.assertIsInstance(case.helper, Helper)
    self.assertIs(case.agent, case.helper.agent)
    first = case.helper
    case.setUp()
    self.assertIsNot(first, case.helper)

  def test_what_is_played_is_noted_step_by_step(self) -> None:
    case = self.case(answers={'open': Container(slots=(WOOL,)),
                              'take': WOOL})
    chest = Handle(MCBlocks.Chest, CHEST)
    outcome = case.play(Verb.OPEN(chest), Verb.TAKE(MCItems.PinkWool),
                        Verb.CLOSE())
    self.assertTrue(outcome.done)
    self.assertEqual([
      'done: open MCBlocks.Chest at (0, 4, 6): it holds 1 minecraft:wool:6',
      'done: take MCItems.PinkWool: 1 minecraft:wool:6 moved',
      'done: close', 'done: 3 steps'], self.notes)

  def test_a_step_not_done_is_the_tests_error(self) -> None:
    stopped = TesttimeError('take', None, 'it is empty')
    case = self.case(stops={'take': stopped})
    with self.assertRaises(TesttimeError) as raised:
      case.play(Verb.TAKE(MCItems.PinkWool))
    self.assertIs(stopped, raised.exception)
    self.assertEqual(1, len(self.notes))


if __name__ == '__main__':
  unittest.main()
