"""
meantwell's ground (SPEC.md 21.7 step 2), without a game: the package is
there under the version its pyproject names, the pyproject names what it
stands on, and the agent it stands on (unittas.agent, SPEC.md 21.6) is
installed with the steps an instruction calls.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import re
import tomllib
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
#  what the package stands on (SPEC.md 21.6)
NEEDS = ('mcdex', 'unittas', 'worktoy')
#  the agent's steps, as unitTAS's README lists them ("Scenarios: an
#  agent that plays"), and the loop's own
STEPS = ('walkTo', 'reach', 'lookAt', 'use', 'breakBlock', 'place',
         'open', 'contents', 'take', 'put', 'close', 'inventory',
         'examine', 'identify', 'wait', 'perceive', 'letGo')


def _project() -> dict:
  """The pyproject's project table."""
  with open(os.path.join(ROOT, 'pyproject.toml'), 'rb') as file:
    return tomllib.load(file)['project']


class GroundTests(unittest.TestCase):
  """The package, its version, its needs and the agent it stands on."""

  def test_the_version_is_the_pyprojects(self) -> None:
    import meantwell
    project = _project()
    self.assertEqual('meantwell', project['name'])
    self.assertEqual(project['version'], meantwell.__version__)

  def test_the_pyproject_names_what_it_stands_on(self) -> None:
    named = sorted(re.split(r'[<>=!~ ]', each, maxsplit=1)[0]
                   for each in _project()['dependencies'])
    self.assertEqual(sorted(NEEDS), named)

  def test_the_agent_is_there_with_its_steps(self) -> None:
    from unittas.agent import Agent
    lacking = [step for step in STEPS
               if not callable(getattr(Agent, step, None))]
    self.assertEqual([], lacking)


if __name__ == '__main__':
  unittest.main()
