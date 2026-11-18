"""
A series of actions in a real game (SPEC.md 21.19 S4), on the practice
instance, written as a unitTAS test writes it: a HelperTestCase, the
scene's own things, short words. The scene is a lever and a chest, put
there by command; the wool is put in the robot's hand by command too.
What is played is the robot's, by a player's means; what came of it is
examined by command, the test's own way. Each step's line is noted under
its test's line in the report.

  unittas run tests.game.test_series
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from mcdex import MCBlocks, MCItems

from meantwell.helpertestcase import HelperTestCase
from meantwell.question import Question
from meantwell.verb import Verb
from unittas.errors import TesttimeError

#  from the scene's origin, the block the run's start stands in
LEVER, CHEST, ASIDE = (5, 0, 7), (0, 0, 6), (4, 0, 2)


class SeriesTests(HelperTestCase):

  #  a guard by the clock, never the verdict
  timeout_seconds = 300

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    #  the setup is by command, not the agent
    cls.lever = cls.scene.place(MCBlocks.Lever, at=LEVER)
    cls.chest = cls.scene.place(MCBlocks.Chest, at=CHEST)

  def held(self, thing: object) -> set:
    """The names of what the thing holds, by command."""
    return {each.name for each in thing.contents()}

  def test_1_it_goes_aside_and_uses_the_lever(self) -> None:
    self.assertFalse(self.lever.isOn())
    self.play(Verb.GO(self.scene.at(ASIDE).center()), Verb.WAIT(5),
              Verb.USE(self.lever))
    self.assertTrue(self.lever.isOn())

  def test_2_wool_put_in_the_chest_and_taken_out_again(self) -> None:
    self.game.setSlot('main.0', MCItems.PinkWool)
    self.play(Verb.OPEN(self.chest), Verb.PUT(MCItems.PinkWool),
              Verb.CLOSE())
    self.assertIn('PinkWool', self.held(self.chest))
    answer = self.play(Verb.OPEN(self.chest), Verb.TAKE(MCItems.PinkWool),
                       Verb.CLOSE(), Question.INVENTORY())
    self.assertNotIn('PinkWool', self.held(self.chest))
    #  the series' last step's answer: its own inventory, as it knows it
    self.assertIn('PinkWool', {each.name for each in answer.value[-1].value})

  def test_3_a_step_it_cant_do_is_the_tests_error(self) -> None:
    with self.assertRaises(TesttimeError) as stopped:
      self.play(Verb.OPEN(self.chest), Verb.TAKE(MCItems.Diamond),
                Verb.CLOSE())
    self.assertEqual('take', stopped.exception.step)
    #  the series stopped there, the chest's screen still open
    self.play(Verb.CLOSE())
