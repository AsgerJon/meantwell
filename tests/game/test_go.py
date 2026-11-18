"""
The helper's 'go' in a real game (SPEC.md 21.11 M2, 21.12), on the
practice instance: an instruction to go, followed on the real agent by
its traveller, there and back. Each line the helper says is noted under
the test's line in the report.

  unittas run tests.game.test_go
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from meantwell.action import Action
from meantwell.helper import Helper
from meantwell.verb import Verb
from unittas.scenario import ScenarioTestCase

#  from the scene's origin, the block the run's start stands in
FAR = (0, 0, 24)


class GoTests(ScenarioTestCase):

  #  a trip is long by the clock too: a guard, never the verdict
  timeout_seconds = 300

  def test_go_there_and_back(self) -> None:
    helper = Helper(self.agent, self.scene.note)
    home = self.agent.perceive().pos
    far = self.scene.at(FAR).center()
    for place in (far, home):
      outcome = helper.follow(Action(Verb.GO, place=place))
      self.assertTrue(outcome.done, outcome.said)
      short = math.hypot(place.x - outcome.value.pos.x,
                         place.z - outcome.value.pos.z)
      self.assertLessEqual(short, 0.25)
    #  the way back is on ground it remembers
    self.assertGreater(helper.traveller.atlas.columns, 17 * 17)
