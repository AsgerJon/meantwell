"""
An action as a value (SPEC.md 21.7 step 3), without a game: a verb, with
the thing (an mcdex member) and the place its verb needs and no others.
One made wrong is refused as it is made. Equal when its parts are,
hashable, and written as a person would say it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from meantwell.action import Action
from meantwell.instruction import Instruction
from meantwell.verb import Verb
from unittas.values import BlockPos, Vec3

LEVER = BlockPos(5, 4, 7)
SPOT = Vec3(6.5, 4.0, 4.5)


class ActionTests(unittest.TestCase):

  def test_each_verb_with_what_it_needs(self) -> None:
    made = [Action(Verb.GO, place=SPOT), Action(Verb.GO, place=LEVER),
            Action(Verb.USE, place=LEVER),
            Action(Verb.USE, MCBlocks.Lever, LEVER),
            Action(Verb.BREAK, MCBlocks.Stone, LEVER),
            Action(Verb.OPEN, MCBlocks.Chest, LEVER),
            Action(Verb.PLACE, MCItems.Stone, LEVER),
            Action(Verb.TAKE, MCItems.PinkWool),
            Action(Verb.PUT, MCItems.Stone),
            Action(Verb.CLOSE), Action(Verb.WAIT, ticks=40)]
    for action in made:
      self.assertIsInstance(action, Instruction)
    self.assertEqual(len(Verb), len(set(each.verb for each in made)))

  def test_a_part_missing_is_refused_as_it_is_made(self) -> None:
    for verb, parts in ((Verb.GO, {}), (Verb.USE, {}), (Verb.BREAK, {}),
                        (Verb.OPEN, {'thing': MCBlocks.Chest}),
                        (Verb.PLACE, {'place': LEVER}),
                        (Verb.PLACE, {'thing': MCItems.Stone}),
                        (Verb.TAKE, {}), (Verb.PUT, {})):
      with self.subTest(verb=verb, parts=parts):
        with self.assertRaises(TypeError) as raised:
          Action(verb, **parts)
        self.assertIn(verb.value, str(raised.exception))

  def test_a_part_too_many_is_refused(self) -> None:
    lever, stone = MCBlocks.Lever, MCItems.Stone
    for verb, parts in ((Verb.GO, {'thing': lever, 'place': SPOT}),
                        (Verb.TAKE, {'thing': stone, 'place': LEVER}),
                        (Verb.CLOSE, {'place': LEVER}),
                        (Verb.CLOSE, {'thing': MCItems.Stone}),
                        (Verb.CLOSE, {'ticks': 5}),
                        (Verb.TAKE, {'thing': MCItems.Stone, 'ticks': 5}),
                        (Verb.WAIT, {'ticks': 5, 'place': LEVER})):
      with self.subTest(verb=verb, parts=parts):
        with self.assertRaises(TypeError):
          Action(verb, **parts)

  def test_a_part_of_the_wrong_kind_is_refused(self) -> None:
    for verb, parts in ((Verb.USE, {'place': SPOT}),
                        (Verb.USE, {'place': (5, 4, 7)}),
                        (Verb.GO, {'place': 'there'}),
                        (Verb.TAKE, {'thing': 'minecraft:wool'}),
                        (Verb.USE, {'thing': 'a lever', 'place': LEVER})):
      with self.subTest(verb=verb, parts=parts):
        with self.assertRaises(TypeError):
          Action(verb, **parts)

  def test_ticks_are_above_0(self) -> None:
    with self.assertRaises(ValueError):
      Action(Verb.WAIT)
    with self.assertRaises(ValueError):
      Action(Verb.WAIT, ticks=-3)
    with self.assertRaises(ValueError):
      Action(Verb.GO, place=SPOT, ticks=-1)
    self.assertEqual(0, Action(Verb.GO, place=SPOT).ticks)

  def test_written_as_a_person_says_it(self) -> None:
    for written, action in (
        ('go to (6.50, 4.00, 4.50)', Action(Verb.GO, place=SPOT)),
        ('go to (5, 4, 7)', Action(Verb.GO, place=LEVER)),
        ('go to (5, 4, 7), within 200 ticks',
         Action(Verb.GO, place=LEVER, ticks=200)),
        ('use the block at (5, 4, 7)', Action(Verb.USE, place=LEVER)),
        ('use MCBlocks.Lever at (5, 4, 7)',
         Action(Verb.USE, MCBlocks.Lever, LEVER)),
        ('break MCBlocks.Stone at (5, 4, 7)',
         Action(Verb.BREAK, MCBlocks.Stone, LEVER)),
        ('open MCBlocks.Chest at (5, 4, 7)',
         Action(Verb.OPEN, MCBlocks.Chest, LEVER)),
        ('place MCItems.Stone at (5, 4, 7)',
         Action(Verb.PLACE, MCItems.Stone, LEVER)),
        ('take MCItems.PinkWool', Action(Verb.TAKE, MCItems.PinkWool)),
        ('put MCItems.Stone', Action(Verb.PUT, MCItems.Stone)),
        ('close', Action(Verb.CLOSE)),
        ('wait 40 ticks', Action(Verb.WAIT, ticks=40))):
      self.assertEqual(written, str(action))

  def test_equal_when_its_parts_are_and_hashable(self) -> None:
    one = Action(Verb.USE, MCBlocks.Lever, LEVER)
    self.assertEqual(one, Action(Verb.USE, MCBlocks.Lever,
                                 BlockPos(5, 4, 7)))
    self.assertNotEqual(one, Action(Verb.BREAK, MCBlocks.Lever, LEVER))
    self.assertEqual(1, len({one, Action(Verb.USE, MCBlocks.Lever, LEVER)}))

  def test_a_verb_by_its_word(self) -> None:
    self.assertEqual(Action(Verb.TAKE, MCItems.PinkWool),
                     Action('take', MCItems.PinkWool))

  def test_it_cant_be_changed(self) -> None:
    with self.assertRaises(AttributeError):
      Action(Verb.CLOSE).ticks = 5


if __name__ == '__main__':
  unittest.main()
