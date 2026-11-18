"""
A question called with its examination's parts makes the examination
(SPEC.md 21.19 S1), the same value as made by hand. What a block is, is
asked of a place, or of a thing with its own place (handle.py); the
candidates are told as 'among'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks

from handle import Handle
from meantwell.examination import Examination
from meantwell.question import Question
from unittas.values import BlockPos, Vec3

STONE = BlockPos(3, 4, 6)
AMONG = (MCBlocks.Stone, MCBlocks.Bedrock)


class QuestionTests(unittest.TestCase):

  def test_each_question_has_its_short_word(self) -> None:
    stone = Handle(MCBlocks.Stone, STONE)
    for told, byHand in (
        (Question.INVENTORY(), Examination(Question.INVENTORY)),
        (Question.CONTENTS(), Examination(Question.CONTENTS)),
        (Question.IDENTIFY(STONE), Examination(Question.IDENTIFY, STONE)),
        (Question.IDENTIFY(stone), Examination(Question.IDENTIFY, STONE)),
        (Question.IDENTIFY(stone, among=AMONG),
         Examination(Question.IDENTIFY, STONE, AMONG)),
        (Question.IDENTIFY(STONE, among=list(AMONG)),
         Examination(Question.IDENTIFY, STONE, AMONG))):
      with self.subTest(examination=str(byHand)):
        self.assertEqual(byHand, told)
        self.assertEqual(str(byHand), str(told))

  def test_what_its_question_refuses_is_refused(self) -> None:
    for question, parts, more in (
        (Question.INVENTORY, (STONE,), {}),
        (Question.CONTENTS, (), {'among': AMONG}),
        (Question.IDENTIFY, (), {}),
        (Question.IDENTIFY, (STONE, STONE), {}),
        (Question.IDENTIFY, (MCBlocks.Stone,), {}),
        (Question.IDENTIFY, (Vec3(3.5, 4.0, 6.5),), {}),
        (Question.IDENTIFY, ('stone',), {}),
        (Question.IDENTIFY, (STONE,), {'among': ('stone',)})):
      with self.subTest(question=question.value, parts=parts):
        with self.assertRaises(TypeError):
          question(*parts, **more)


if __name__ == '__main__':
  unittest.main()
