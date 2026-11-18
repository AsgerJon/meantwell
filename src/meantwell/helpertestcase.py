"""
HelperTestCase: meantwell's front for unitTAS's tests (SPEC.md 21.19
S3). A scenario's tests, each with a helper of its own on the scenario's
agent, so that a test plays a series of actions written in short words,
by the scene's own things:

  class ChestTests(HelperTestCase):

    def test_the_wool_is_taken(self) -> None:
      chest = self.scene.thing(MCBlocks.Chest, at=(0, 0, 6))
      self.play(Verb.OPEN(chest), Verb.TAKE(MCItems.PinkWool),
                Verb.CLOSE())

Each step's line is noted under the test's line in the report. A step
the agent can't complete is the test's ERROR, by the agent's own
TesttimeError. Setup, and examinations by command, stay the test's own
Python around what it plays.

This is the one module of meantwell that takes a test case of unitTAS's
(test_ties holds it to that): nothing else here needs unitTAS's testing,
and whoever instructs the helper without a test never imports this.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from unittas.scenario import ScenarioTestCase

from .helper import Helper

if TYPE_CHECKING:  # pragma: no cover
  from .instruction import Instruction
  from .outcome import Outcome


class HelperTestCase(ScenarioTestCase):
  """
  A scenario's tests with a helper: 'self.helper' follows instructions
  on 'self.agent' and says each line to the scene's notes; a new one
  each test, so that no test goes by what another was shown of the
  ground. 'self.play(...)' is what the helper must do.
  """

  helper: Helper = None

  def setUp(self) -> None:
    super().setUp()
    self.helper = Helper(self.agent, self.scene.note)

  def play(self, *instructions: Instruction) -> Outcome:
    """
    The instructions played by the helper, several as a series, each
    step's line noted: its outcome, done. A step not done raises the
    agent's own TesttimeError, the test's ERROR.
    """
    return self.helper.must(*instructions)
