"""
A conditional instruction (SPEC.md 21.7 step 3; unitTAS's SPEC.md 15.1:
"actions, possibly conditional on anything"), without a game: the agent
is asked first (its inventory, or what a block is by its looks), and
what follows depends on whether the answer holds the thing named. The
examination not done is the conditional not done: it couldn't find out.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from meantwell.action import Action
from meantwell.examination import Examination
from meantwell.helper import Helper
from meantwell.instruction import Instruction
from meantwell.question import Question
from meantwell.verb import Verb
from meantwell.when import When
from recorder import Recorder
from unittas.errors import TesttimeError
from unittas.perception import Perception
from unittas.values import BlockPos, Item

STONE = BlockPos(3, 4, 6)
SEEN = Perception()
WOOL = Item('minecraft:wool', 1, 6)
INVENTORY = Examination(Question.INVENTORY)
LOOKS = Examination(Question.IDENTIFY, STONE)
PUT = Action(Verb.PUT, MCItems.PinkWool)
CLOSE = Action(Verb.CLOSE)
BREAK = Action(Verb.BREAK, MCBlocks.Stone, STONE)
HOLDS = 'when its inventory holds MCItems.PinkWool'


class WhenTests(unittest.TestCase):

  def setUp(self) -> None:
    self.said = []

  def follow(self, instruction, **agent) -> tuple:
    recorder = Recorder(**agent)
    outcome = Helper(recorder, self.said.append).follow(instruction)
    return outcome, [step for step, _, _ in recorder.asked]

  def test_a_conditional_is_an_instruction(self) -> None:
    when = When(INVENTORY, MCItems.PinkWool, PUT)
    self.assertIsInstance(when, Instruction)
    self.assertEqual(HOLDS + ': put MCItems.PinkWool', str(when))
    self.assertEqual(HOLDS + ': put MCItems.PinkWool; otherwise: close',
                     str(When(INVENTORY, MCItems.PinkWool, PUT, CLOSE)))
    self.assertEqual('when the block at (3, 4, 6) is MCBlocks.Stone: break '
                     'MCBlocks.Stone at (3, 4, 6)',
                     str(When(LOOKS, MCBlocks.Stone, BREAK)))
    self.assertEqual(when, When(INVENTORY, MCItems.PinkWool, PUT))

  def test_made_wrong_it_is_refused(self) -> None:
    for parts in ((PUT, MCItems.PinkWool, PUT),
                  (INVENTORY, 'minecraft:wool', PUT),
                  (INVENTORY, MCItems.PinkWool, 'put it'),
                  (INVENTORY, MCItems.PinkWool, PUT, 'close'),
                  (Examination(Question.CONTENTS), MCItems.PinkWool, PUT)):
      with self.subTest(parts=parts):
        with self.assertRaises(TypeError):
          When(*parts)

  def test_it_holds_so_what_follows_is_followed(self) -> None:
    outcome, asked = self.follow(
      When(INVENTORY, MCItems.PinkWool, PUT, CLOSE),
      answers={'inventory': frozenset({MCItems.PinkWool}), 'put': WOOL})
    self.assertEqual(['inventory', 'put'], asked)
    self.assertTrue(outcome.done)
    self.assertEqual(['done: inventory: MCItems.PinkWool',
                      'done: put MCItems.PinkWool: 1 minecraft:wool:6 moved',
                      'done: ' + HOLDS + ': it does'], self.said)
    self.assertEqual([INVENTORY, PUT],
                     [each.instruction for each in outcome.value])

  def test_it_doesnt_so_the_other_is_followed(self) -> None:
    outcome, asked = self.follow(
      When(INVENTORY, MCItems.PinkWool, PUT, CLOSE),
      answers={'inventory': frozenset({MCItems.Stone})})
    self.assertEqual(['inventory', 'close'], asked)
    self.assertTrue(outcome.done)
    self.assertEqual('done: ' + HOLDS + ': it does not', self.said[-1])

  def test_it_doesnt_and_nothing_follows(self) -> None:
    outcome, asked = self.follow(
      When(INVENTORY, MCItems.PinkWool, PUT),
      answers={'inventory': frozenset()})
    self.assertEqual(['inventory'], asked)
    self.assertTrue(outcome.done)
    self.assertEqual(['done: inventory: nothing',
                      'done: ' + HOLDS + ': it does not'], self.said)
    self.assertEqual(1, len(outcome.value))

  def test_by_a_blocks_looks(self) -> None:
    for found, asked in ((MCBlocks.Stone, ['identify', 'breakBlock']),
                         (MCBlocks.Bedrock, ['identify'])):
      with self.subTest(found=found):
        outcome, was = self.follow(When(LOOKS, MCBlocks.Stone, BREAK),
                                   answers={'identify': found,
                                            'breakBlock': SEEN})
        self.assertEqual(asked, was)
        self.assertTrue(outcome.done)

  def test_what_follows_not_done(self) -> None:
    error = TesttimeError('put', None, 'no room on the other side')
    outcome, asked = self.follow(
      When(INVENTORY, MCItems.PinkWool, PUT),
      answers={'inventory': frozenset({MCItems.PinkWool})},
      stops={'put': error})
    self.assertEqual(['inventory', 'put'], asked)
    self.assertFalse(outcome.done)
    self.assertIs(error, outcome.error)
    self.assertEqual('not done: ' + HOLDS + ': it does, and what followed '
                     'was not done', self.said[-1])

  def test_it_couldnt_find_out(self) -> None:
    error = TesttimeError('identify', None, 'no side shows the block')
    outcome, asked = self.follow(When(LOOKS, MCBlocks.Stone, BREAK),
                                 stops={'identify': error})
    self.assertEqual(['identify'], asked)
    self.assertFalse(outcome.done)
    self.assertIs(error, outcome.error)
    self.assertEqual('not done: when the block at (3, 4, 6) is '
                     'MCBlocks.Stone: it could not find out', self.said[-1])


if __name__ == '__main__':
  unittest.main()
