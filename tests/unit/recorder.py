"""
Recorder: an agent that only records what it is asked, for the tests of
what follows instructions (SPEC.md 21.7 step 3; not a test module
itself). Each of the agent's steps is noted with its arguments, in
order. A step gives back the answer set for it, or raises what was set
to stop it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Any, Callable, Optional

from test_ground import STEPS


class Recorder:
  """
  An agent, as far as being asked goes.

    agent = Recorder(answers={'inventory': frozenset()},
                     stops={'take': TesttimeError('take', None, 'none')})
    agent.take(MCItems.PinkWool)  # raises, after being noted
    agent.asked  # [('take', (MCItems.PinkWool,), {})]
  """

  def __init__(self, answers: Optional[dict] = None,
               stops: Optional[dict] = None) -> None:
    for step in list(answers or ()) + list(stops or ()):
      if step not in STEPS:
        raise ValueError('%r is no step of the agent' % (step,))
    self.asked = []
    self.answers = dict(answers or {})
    self.stops = dict(stops or {})

  def __getattr__(self, step: str) -> Callable:
    if step not in STEPS:
      raise AttributeError(step)

    def asked(*args: Any, **kwargs: Any) -> Any:
      self.asked.append((step, args, kwargs))
      if step in self.stops:
        raise self.stops[step]
      return self.answers.get(step)

    return asked
