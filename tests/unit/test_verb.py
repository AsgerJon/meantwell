"""
A verb called with its action's parts makes the action (SPEC.md 21.19
S1): the short words a series is written in. A part is told by its
kind: a thing with its own place (a scene's Thing in unitTAS; here
handle.py), an mcdex member, a place, and for a wait a whole number.
What is made is the same value as the action made by hand. Two parts of
a kind, or a part of another kind, are refused, naming it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from handle import Handle
from meantwell.action import Action
from meantwell.verb import Verb
from unittas.values import BlockPos, Vec3

LEVER = BlockPos(5, 4, 7)
CHEST = BlockPos(0, 4, 6)
STONE = BlockPos(3, 4, 6)
SPOT = Vec3(6.5, 4.0, 4.5)


class VerbTests(unittest.TestCase):

  def test_a_thing_with_its_own_place_is_both_parts(self) -> None:
    lever = Handle(MCBlocks.Lever, LEVER)
    chest = Handle(MCBlocks.Chest, CHEST)
    stone = Handle(MCBlocks.Stone, STONE)
    for told, byHand in (
        (Verb.USE(lever), Action(Verb.USE, MCBlocks.Lever, LEVER)),
        (Verb.OPEN(chest), Action(Verb.OPEN, MCBlocks.Chest, CHEST)),
        (Verb.BREAK(stone), Action(Verb.BREAK, MCBlocks.Stone, STONE)),
        (Verb.USE(lever, ticks=200),
         Action(Verb.USE, MCBlocks.Lever, LEVER, 200))):
      with self.subTest(action=str(byHand)):
        self.assertEqual(byHand, told)
        self.assertEqual(str(byHand), str(told))

  def test_a_member_and_a_place_are_its_parts_in_either_order(self) -> None:
    byHand = Action(Verb.PLACE, MCItems.Stone, STONE)
    self.assertEqual(byHand, Verb.PLACE(MCItems.Stone, STONE))
    self.assertEqual(byHand, Verb.PLACE(STONE, MCItems.Stone))
    self.assertEqual(Action(Verb.USE, place=LEVER), Verb.USE(LEVER))

  def test_each_verb_has_its_short_word(self) -> None:
    for told, byHand in (
        (Verb.GO(SPOT), Action(Verb.GO, place=SPOT)),
        (Verb.GO(STONE, ticks=300), Action(Verb.GO, place=STONE,
                                           ticks=300)),
        (Verb.TAKE(MCItems.PinkWool), Action(Verb.TAKE, MCItems.PinkWool)),
        (Verb.PUT(MCItems.Stone), Action(Verb.PUT, MCItems.Stone)),
        (Verb.CLOSE(), Action(Verb.CLOSE)),
        (Verb.WAIT(40), Action(Verb.WAIT, ticks=40)),
        (Verb.WAIT(ticks=40), Action(Verb.WAIT, ticks=40))):
      with self.subTest(action=str(byHand)):
        self.assertEqual(byHand, told)

  def test_what_its_verb_refuses_is_refused_as_by_hand(self) -> None:
    lever = Handle(MCBlocks.Lever, LEVER)
    for verb, parts in ((Verb.GO, (lever,)), (Verb.TAKE, (lever,)),
                        (Verb.CLOSE, (LEVER,)), (Verb.USE, ()),
                        (Verb.PLACE, (STONE,)), (Verb.WAIT, ())):
      with self.subTest(verb=verb.value, parts=parts):
        with self.assertRaises((TypeError, ValueError)):
          verb(*parts)

  def test_two_parts_of_a_kind_are_refused(self) -> None:
    lever = Handle(MCBlocks.Lever, LEVER)
    for parts, named in (((LEVER, STONE), 'two places'),
                         ((MCItems.Stone, MCItems.PinkWool), 'two things'),
                         ((lever, STONE), 'two places'),
                         ((MCItems.Stone, lever), 'two things')):
      with self.subTest(parts=named):
        with self.assertRaises(TypeError) as refused:
          Verb.PLACE(*parts)
        self.assertIn(named, str(refused.exception))
        self.assertIn('place', str(refused.exception))

  def test_a_part_of_another_kind_is_refused_and_named(self) -> None:
    for part in ('lever', 4.5, True, None, (5, 4, 7)):
      with self.subTest(part=part):
        with self.assertRaises(TypeError) as refused:
          Verb.USE(part)
        self.assertIn(repr(part), str(refused.exception))

  def test_a_whole_number_is_a_waits_ticks_alone(self) -> None:
    with self.assertRaises(TypeError) as refused:
      Verb.USE(LEVER, 200)
    self.assertIn('ticks=', str(refused.exception))
    with self.assertRaises(TypeError):
      Verb.WAIT(40, ticks=40)
    with self.assertRaises(TypeError):
      Verb.WAIT(40, 40)

  def test_a_things_truth_is_never_asked(self) -> None:
    #  handle.py fails whoever asks; in unitTAS it is a command
    Verb.OPEN(Handle(MCBlocks.Chest, CHEST))


if __name__ == '__main__':
  unittest.main()
