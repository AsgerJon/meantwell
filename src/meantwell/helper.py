"""
Helper: what follows instructions (SPEC.md 21.7 step 3): an agent, and
someone to tell. Following an instruction asks the agent's own steps,
and what comes of it is said and given back (SPEC.md 21.3: it says what
it did and saw). To go is a trip by its traveller, however far (SPEC.md
21.11). The helper never holds a game: the agent is all it has of one.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from unittas.errors import TesttimeError

from .action import Action
from .examination import Examination
from .instruction import Instruction
from .outcome import Outcome
from .question import Question
from .steps import Steps
from .traveller import Traveller
from .verb import Verb
from .when import When
from .words import met, named, stack, stacks, where

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable

  from unittas.agent import Agent


class Helper(BaseObject):
  """
  The helper of one agent. Each instruction it follows ends in an
  Outcome, whose line goes to the listener it was made with: a report, a
  terminal, the chat. A step the agent can't complete (its
  TesttimeError) is an outcome not done, naming the step and why.
  Anything else that goes wrong is raised: a game that is gone, or an
  instruction the agent's step refuses, is no outcome of the step. What
  its traveller was shown of the ground on one trip, it remembers on the
  next.

    helper = Helper(agent, print)
    helper.follow(Action(Verb.USE, MCBlocks.Lever, BlockPos(5, 4, 7)))
    # done: use MCBlocks.Lever at (5, 4, 7): at (5.50, 4.00, 5.02), the
    # crosshair on minecraft:lever at (5, 4, 7)
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  #  The agent that carries the instructions out
  __agent__: Agent = None
  #  Whom each outcome's line is said to
  __say__: Callable = None
  #  The agent's traveller, which goes where it is told to go
  __traveller__: Traveller = None

  #  Public Variables
  agent = Field()
  traveller = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @agent.GET
  def _getAgent(self) -> Agent:
    """The agent that carries the instructions out."""
    return self.__agent__

  @traveller.GET
  def _getTraveller(self) -> Traveller:
    """The agent's traveller, with what it remembers of the ground."""
    return self.__traveller__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, agent: Agent, say: Callable[[str], Any]) -> None:
    """
    The helper of 'agent', saying each outcome's line to 'say' (called
    with the line).
    """
    BaseObject.__init__(self)
    if not callable(say):
      raise TypeError('a helper is made with someone to tell, called with '
                      'each line, not %r' % (say,))
    self.__agent__ = agent
    self.__say__ = say
    self.__traveller__ = Traveller(agent)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def follow(self, instruction: Instruction) -> Outcome:
    """
    Follows the instruction, and says what came of it. A series says
    each of its steps as it ends, then itself.

    Parameters
    ----------
    instruction : Instruction
      An Action, an Examination, a Steps or a When.

    Returns
    -------
    Outcome
      Done or not, the line said, what the agent gave, and the agent's
      error when it wasn't done.

    Raises
    ------
    TypeError
      What it is given is no instruction it follows.
    """
    if isinstance(instruction, Steps):
      outcome = self._series(instruction)
    elif isinstance(instruction, When):
      outcome = self._when(instruction)
    elif isinstance(instruction, Action):
      outcome = self._one(instruction, self._act)
    elif isinstance(instruction, Examination):
      outcome = self._one(instruction, self._examine)
    else:
      raise TypeError('the helper follows an Action, an Examination, a '
                      'Steps or a When, not %r' % (instruction,))
    self.__say__(outcome.said)
    return outcome

  def _one(self, instruction: Instruction, how: Callable) -> Outcome:
    """One step of the agent's, by 'how': done, or not done and why."""
    try:
      value, saw = how(instruction)
    except TesttimeError as error:
      said = 'not done: %s: %s' % (instruction, error)
      return Outcome(instruction, False, said, None, error)
    said = 'done: %s' % (instruction,)
    if saw:
      said += ': %s' % saw
    return Outcome(instruction, True, said, value)

  def _act(self, action: Action) -> tuple:
    """The agent's step for the action: (what it gave, what it saw)."""
    agent, verb = self.__agent__, action.verb
    budget = {'ticks': action.ticks} if action.ticks else {}
    if verb is Verb.WAIT:
      agent.wait(action.ticks)
      return None, ''
    if verb is Verb.CLOSE:
      agent.close()
      return None, ''
    if verb is Verb.GO:
      seen = self.__traveller__.travel(action.place, **budget)
      return seen, 'at %s' % where(seen.pos)
    if verb is Verb.TAKE:
      moved = agent.take(action.thing)
      return moved, '%s moved' % stack(moved)
    if verb is Verb.PUT:
      moved = agent.put(action.thing)
      return moved, '%s moved' % stack(moved)
    if verb is Verb.OPEN:
      shown = agent.open(action.place, **budget)
      held = stacks(shown.contents)
      return shown, ('it is empty' if held == 'nothing'
                     else 'it holds %s' % held)
    if verb is Verb.USE:
      seen = agent.use(action.place, **budget)
    elif verb is Verb.BREAK:
      seen = agent.breakBlock(action.place, **budget)
    elif verb is Verb.PLACE:
      seen = agent.place(action.place, action.thing, **budget)
    else:
      raise TypeError('the helper has no step for the verb %r' % (verb,))
    return seen, 'at %s, the crosshair on %s' % (where(seen.pos),
                                                 met(seen.target))

  def _examine(self, examination: Examination) -> tuple:
    """The agent's own examination: (its answer, the answer as said)."""
    agent, asks = self.__agent__, examination.asks
    if asks is Question.INVENTORY:
      held = agent.inventory()
      return held, ', '.join(sorted(named(each) for each in held)) or (
        'nothing')
    if asks is Question.CONTENTS:
      shown = agent.contents()
      return shown, stacks(shown)
    if asks is Question.IDENTIFY:
      among = {'among': examination.among} if examination.among else {}
      found = agent.identify(examination.place, **among)
      return found, named(found)
    raise TypeError('the helper has no step for the question %r' % (asks,))

  def _series(self, series: Steps) -> Outcome:
    """Each step in turn, to the first not done."""
    outcomes = []
    for at, step in enumerate(series.steps):
      outcome = self.follow(step)
      outcomes.append(outcome)
      if not outcome.done:
        said = 'not done: %s: stopped at step %d, %s' % (series, at + 1,
                                                         step)
        return Outcome(series, False, said, tuple(outcomes), outcome.error)
    return Outcome(series, True, 'done: %s' % (series,), tuple(outcomes))

  def _when(self, when: When) -> Outcome:
    """The examination, then what follows its answer."""
    asked = self.follow(when.asks)
    head = 'when %s' % when.condition
    if not asked.done:
      said = 'not done: %s: it could not find out' % head
      return Outcome(when, False, said, (asked,), asked.error)
    so = when.isSo(asked.value)
    does = 'it does' if so else 'it does not'
    after = when.then if so else when.otherwise
    if after is None:
      return Outcome(when, True, 'done: %s: %s' % (head, does), (asked,))
    followed = self.follow(after)
    if not followed.done:
      said = 'not done: %s: %s, and what followed was not done' % (head,
                                                                   does)
      return Outcome(when, False, said, (asked, followed), followed.error)
    return Outcome(when, True, 'done: %s: %s' % (head, does),
                   (asked, followed))
