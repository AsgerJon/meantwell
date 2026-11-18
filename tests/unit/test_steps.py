"""
A series of instructions (SPEC.md 21.7 step 3), without a game: followed
in order on an agent that only records (recorder.py), each step's
outcome said as it ends. The series stops at the first step not done,
since the steps after it count on it, and says where it stopped.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from meantwell.action import Action
from meantwell.helper import Helper
from meantwell.instruction import Instruction
from meantwell.steps import Steps
from meantwell.verb import Verb
from recorder import Recorder
from unittas.container import Container
from unittas.errors import TesttimeError
from unittas.values import BlockPos, Item

CHEST = BlockPos(0, 4, 6)
WOOL = Item('minecraft:wool', 1, 6)
OPEN = Action(Verb.OPEN, MCBlocks.Chest, CHEST)
TAKE = Action(Verb.TAKE, MCItems.PinkWool)
CLOSE = Action(Verb.CLOSE)
ANSWERS = {'open': Container(slots=(WOOL,)), 'take': WOOL}


class StepsTests(unittest.TestCase):

  def setUp(self) -> None:
    self.said = []

  def test_a_series_is_an_instruction_of_instructions(self) -> None:
    series = Steps((OPEN, TAKE, CLOSE))
    self.assertIsInstance(series, Instruction)
    self.assertEqual((OPEN, TAKE, CLOSE), series.steps)
    self.assertEqual('3 steps', str(series))
    self.assertEqual('1 step', str(Steps((CLOSE,))))
    self.assertEqual(series, Steps((OPEN, TAKE, CLOSE)))
    self.assertIsInstance(Steps((series, CLOSE)), Instruction)

  def test_made_wrong_it_is_refused(self) -> None:
    for wrong in ((), (OPEN, 'take the wool'), (None,)):
      with self.subTest(wrong=wrong):
        with self.assertRaises(TypeError):
          Steps(wrong)

  def test_followed_in_order_each_said(self) -> None:
    recorder = Recorder(answers=ANSWERS)
    series = Steps((OPEN, TAKE, CLOSE))
    outcome = Helper(recorder, self.said.append).follow(series)
    self.assertEqual(['open', 'take', 'close'],
                     [step for step, _, _ in recorder.asked])
    self.assertEqual([
      'done: open MCBlocks.Chest at (0, 4, 6): it holds 1 minecraft:wool:6',
      'done: take MCItems.PinkWool: 1 minecraft:wool:6 moved',
      'done: close', 'done: 3 steps'], self.said)
    self.assertTrue(outcome.done)
    self.assertEqual('done: 3 steps', outcome.said)
    self.assertEqual([OPEN, TAKE, CLOSE],
                     [each.instruction for each in outcome.value])
    self.assertTrue(all(each.done for each in outcome.value))

  def test_it_stops_at_the_first_step_not_done(self) -> None:
    error = TesttimeError('take', None, 'no MCItems.PinkWool in the '
                          'container (minecraft:stone)')
    recorder = Recorder(answers=ANSWERS, stops={'take': error})
    outcome = Helper(recorder, self.said.append).follow(
      Steps((OPEN, TAKE, CLOSE)))
    self.assertEqual(['open', 'take'],
                     [step for step, _, _ in recorder.asked])
    self.assertFalse(outcome.done)
    self.assertIs(error, outcome.error)
    self.assertEqual([True, False], [each.done for each in outcome.value])
    self.assertEqual(
      'not done: 3 steps: stopped at step 2, take MCItems.PinkWool',
      self.said[-1])
    self.assertEqual(3, len(self.said))

  def test_a_series_within_a_series(self) -> None:
    recorder = Recorder(answers=ANSWERS)
    outcome = Helper(recorder, self.said.append).follow(
      Steps((Steps((OPEN, TAKE)), CLOSE)))
    self.assertTrue(outcome.done)
    self.assertEqual(['open', 'take', 'close'],
                     [step for step, _, _ in recorder.asked])
    self.assertEqual(['done: 2 steps', 'done: close', 'done: 2 steps'],
                     self.said[2:])


if __name__ == '__main__':
  unittest.main()
