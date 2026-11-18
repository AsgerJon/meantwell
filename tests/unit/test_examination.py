"""
An examination as a value (SPEC.md 21.7 step 3), without a game: what
the agent is asked about, by its own means alone (its inventory, the
open container as its screen shows it, what a block is by its looks),
with the place and the candidates its question needs and no others.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from meantwell.examination import Examination
from meantwell.instruction import Instruction
from meantwell.question import Question
from unittas.values import BlockPos, Vec3

STONE = BlockPos(3, 4, 6)
FEW = (MCBlocks.Stone, MCBlocks.Bedrock)


class ExaminationTests(unittest.TestCase):

  def test_each_question_with_what_it_needs(self) -> None:
    made = [Examination(Question.INVENTORY), Examination(Question.CONTENTS),
            Examination(Question.IDENTIFY, STONE),
            Examination(Question.IDENTIFY, STONE, FEW)]
    for examination in made:
      self.assertIsInstance(examination, Instruction)
    self.assertEqual(len(Question), len(set(each.asks for each in made)))

  def test_made_wrong_it_is_refused(self) -> None:
    for asks, parts in ((Question.IDENTIFY, {}),
                        (Question.IDENTIFY, {'place': Vec3(3.5, 4.0, 6.5)}),
                        (Question.IDENTIFY, {'place': STONE,
                                             'among': (MCItems.Stone, 'x')}),
                        (Question.INVENTORY, {'place': STONE}),
                        (Question.CONTENTS, {'among': FEW})):
      with self.subTest(asks=asks, parts=parts):
        with self.assertRaises(TypeError) as raised:
          Examination(asks, **parts)
        self.assertIn(asks.value, str(raised.exception))

  def test_written_as_a_person_says_it(self) -> None:
    for written, examination in (
        ('inventory', Examination(Question.INVENTORY)),
        ('contents', Examination(Question.CONTENTS)),
        ('identify the block at (3, 4, 6)',
         Examination(Question.IDENTIFY, STONE)),
        ('identify the block at (3, 4, 6) among MCBlocks.Stone, '
         'MCBlocks.Bedrock', Examination(Question.IDENTIFY, STONE, FEW))):
      self.assertEqual(written, str(examination))

  def test_equal_when_its_parts_are_and_hashable(self) -> None:
    one = Examination(Question.IDENTIFY, STONE, FEW)
    self.assertEqual(one, Examination('identify', BlockPos(3, 4, 6), FEW))
    self.assertNotEqual(one, Examination(Question.IDENTIFY, STONE))
    self.assertEqual(1, len({one, Examination(Question.IDENTIFY, STONE,
                                              FEW)}))


if __name__ == '__main__':
  unittest.main()
