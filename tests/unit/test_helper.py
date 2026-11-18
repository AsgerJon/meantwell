"""
The helper following an action or an examination (SPEC.md 21.7 step 3),
without a game, on an agent that only records what it is asked
(recorder.py). Each instruction asks the agent's own step, with its
parts; to go is a trip by the helper's traveller, however far (SPEC.md
21.11, M2), tried here in the grid agent's world (gridworld.py). What
comes of it is said to the helper's listener and given back:
done, with what the agent saw; or not done, with the step and why, when
the agent couldn't complete it (TesttimeError). It never says done of a
step the agent didn't complete, and anything else that goes wrong is
raised, not said.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from mcdex import MCBlocks, MCItems

from gridworld import GROUND, GridAgent, arena, wall
from meantwell.action import Action
from meantwell.examination import Examination
from meantwell.helper import Helper
from meantwell.outcome import Outcome
from meantwell.question import Question
from meantwell.traveller import Traveller
from meantwell.verb import Verb
from recorder import Recorder
from unittas.container import Container
from unittas.errors import TesttimeError
from unittas.perception import Perception
from unittas.target import Target
from unittas.values import BlockPos, Item, Vec3

LEVER = BlockPos(5, 4, 7)
CHEST = BlockPos(0, 4, 6)
STONE = BlockPos(3, 4, 6)
SPOT = Vec3(6.5, 4.0, 4.5)
WOOL = Item('minecraft:wool', 1, 6)
#  where the agent stands, its crosshair on the lever
SEEN = Perception(tick=40, pos=Vec3(5.5, 4.0, 5.02), target=Target(
  kind='block', pos=LEVER, id='minecraft:lever'))
THERE = 'at (5.50, 4.00, 5.02)'
MET = THERE + ', the crosshair on minecraft:lever at (5, 4, 7)'


class HelperTests(unittest.TestCase):

  def setUp(self) -> None:
    self.said = []

  def follow(self, instruction, **agent) -> tuple:
    """The instruction followed on a recorder: (outcome, what was asked)."""
    recorder = Recorder(**agent)
    outcome = Helper(recorder, self.said.append).follow(instruction)
    return outcome, recorder.asked

  def test_each_action_asks_the_agents_own_step(self) -> None:
    for action, asked in (
        (Action(Verb.USE, MCBlocks.Lever, LEVER), ('use', (LEVER,), {})),
        (Action(Verb.BREAK, place=STONE), ('breakBlock', (STONE,), {})),
        (Action(Verb.PLACE, MCItems.Stone, STONE),
         ('place', (STONE, MCItems.Stone), {})),
        (Action(Verb.OPEN, MCBlocks.Chest, CHEST), ('open', (CHEST,), {})),
        (Action(Verb.TAKE, MCItems.PinkWool),
         ('take', (MCItems.PinkWool,), {})),
        (Action(Verb.PUT, MCItems.Stone), ('put', (MCItems.Stone,), {})),
        (Action(Verb.CLOSE), ('close', (), {})),
        (Action(Verb.WAIT, ticks=40), ('wait', (40,), {}))):
      with self.subTest(action=str(action)):
        outcome, was = self.follow(action, answers={
          'use': SEEN, 'breakBlock': SEEN, 'place': SEEN,
          'open': Container(slots=(WOOL,)), 'take': WOOL, 'put': WOOL})
        self.assertEqual([asked], was)
        self.assertTrue(outcome.done)

  def test_a_tick_budget_goes_with_the_step(self) -> None:
    for action, asked in (
        (Action(Verb.USE, place=LEVER, ticks=90),
         ('use', (LEVER,), {'ticks': 90})),
        (Action(Verb.BREAK, place=STONE, ticks=50),
         ('breakBlock', (STONE,), {'ticks': 50})),
        (Action(Verb.PLACE, MCItems.Stone, STONE, 70),
         ('place', (STONE, MCItems.Stone), {'ticks': 70})),
        (Action(Verb.OPEN, place=CHEST, ticks=60),
         ('open', (CHEST,), {'ticks': 60}))):
      with self.subTest(action=str(action)):
        _, was = self.follow(action, answers={
          'use': SEEN, 'breakBlock': SEEN, 'place': SEEN,
          'open': Container(slots=(WOOL,))})
        self.assertEqual([asked], was)

  def test_each_examination_asks_the_agents_own(self) -> None:
    few = (MCBlocks.Stone, MCBlocks.Bedrock)
    for examination, asked in (
        (Examination(Question.INVENTORY), ('inventory', (), {})),
        (Examination(Question.CONTENTS), ('contents', (), {})),
        (Examination(Question.IDENTIFY, STONE), ('identify', (STONE,), {})),
        (Examination(Question.IDENTIFY, STONE, few),
         ('identify', (STONE,), {'among': few}))):
      with self.subTest(examination=str(examination)):
        outcome, was = self.follow(examination, answers={
          'inventory': frozenset(), 'contents': (),
          'identify': MCBlocks.Stone})
        self.assertEqual([asked], was)
        self.assertTrue(outcome.done)

  def test_done_says_what_the_agent_saw(self) -> None:
    modern = Item('minecraft:pink_wool', 2, -1)
    for said, instruction, answers in (
        ('done: use MCBlocks.Lever at (5, 4, 7): ' + MET,
         Action(Verb.USE, MCBlocks.Lever, LEVER), {'use': SEEN}),
        ('done: break the block at (3, 4, 6): ' + THERE +
         ', the crosshair on nothing within reach',
         Action(Verb.BREAK, place=STONE),
         {'breakBlock': Perception(pos=SEEN.pos)}),
        ('done: place MCItems.Stone at (3, 4, 6): ' + THERE +
         ', the crosshair on minecraft:pig (entity 7)',
         Action(Verb.PLACE, MCItems.Stone, STONE),
         {'place': Perception(pos=SEEN.pos, target=Target(
           kind='entity', entity=7, type='minecraft:pig'))}),
        ('done: open MCBlocks.Chest at (0, 4, 6): it holds 1 '
         'minecraft:wool:6, 2 minecraft:pink_wool',
         Action(Verb.OPEN, MCBlocks.Chest, CHEST),
         {'open': Container(slots=(WOOL, Item.EMPTY, modern))}),
        ('done: open the block at (0, 4, 6): it is empty',
         Action(Verb.OPEN, place=CHEST),
         {'open': Container(slots=(Item.EMPTY, Item.EMPTY))}),
        ('done: take MCItems.PinkWool: 1 minecraft:wool:6 moved',
         Action(Verb.TAKE, MCItems.PinkWool), {'take': WOOL}),
        ('done: put MCItems.PinkWool: 2 minecraft:pink_wool moved',
         Action(Verb.PUT, MCItems.PinkWool), {'put': modern}),
        ('done: close', Action(Verb.CLOSE), {}),
        ('done: wait 40 ticks', Action(Verb.WAIT, ticks=40), {}),
        ('done: inventory: MCItems.PinkWool, MCItems.Stone',
         Examination(Question.INVENTORY),
         {'inventory': frozenset({MCItems.Stone, MCItems.PinkWool})}),
        ('done: inventory: nothing', Examination(Question.INVENTORY),
         {'inventory': frozenset()}),
        ('done: contents: 1 minecraft:wool:6',
         Examination(Question.CONTENTS), {'contents': (WOOL, Item.EMPTY)}),
        ('done: contents: nothing', Examination(Question.CONTENTS),
         {'contents': (Item.EMPTY,)}),
        ('done: identify the block at (3, 4, 6): MCBlocks.Stone',
         Examination(Question.IDENTIFY, STONE),
         {'identify': MCBlocks.Stone})):
      with self.subTest(said=said):
        self.said.clear()
        outcome, _ = self.follow(instruction, answers=answers)
        self.assertEqual([said], self.said)
        self.assertEqual(Outcome(instruction, True, said,
                                 answers.get(next(iter(answers), None))),
                         outcome)

  def test_not_done_says_the_step_and_why(self) -> None:
    error = TesttimeError(
      'take', SEEN, 'no MCItems.PinkWool in the container (it is empty)')
    action = Action(Verb.TAKE, MCItems.PinkWool)
    outcome, asked = self.follow(action, stops={'take': error})
    said = ('not done: take MCItems.PinkWool: take: no MCItems.PinkWool in '
            'the container (it is empty)')
    self.assertEqual([('take', (MCItems.PinkWool,), {})], asked)
    self.assertEqual([said], self.said)
    self.assertFalse(outcome.done)
    self.assertIs(error, outcome.error)
    self.assertIsNone(outcome.value)
    self.assertEqual(action, outcome.instruction)
    self.assertEqual(said, outcome.said)

  def test_an_examination_not_done(self) -> None:
    error = TesttimeError('identify', SEEN, 'no look beats the next')
    outcome, _ = self.follow(Examination(Question.IDENTIFY, STONE),
                             stops={'identify': error})
    self.assertFalse(outcome.done)
    self.assertEqual(['not done: identify the block at (3, 4, 6): identify: '
                      'no look beats the next'], self.said)

  def test_anything_else_is_raised_and_nothing_said(self) -> None:
    for wrong in (ValueError('a tick budget is above 0'),
                  ConnectionError('the game is gone'), KeyError('slot')):
      with self.subTest(wrong=wrong):
        with self.assertRaises(type(wrong)) as raised:
          self.follow(Action(Verb.USE, place=LEVER), stops={'use': wrong})
        self.assertIs(wrong, raised.exception)
        self.assertEqual([], self.said)

  def test_only_an_instruction_is_followed(self) -> None:
    helper = Helper(Recorder(), self.said.append)
    for wrong in ('take MCItems.PinkWool', None, Verb.CLOSE, 5):
      with self.subTest(wrong=wrong):
        with self.assertRaises(TypeError):
          helper.follow(wrong)
    self.assertEqual([], self.said)

  def test_it_is_made_with_someone_to_tell(self) -> None:
    with self.assertRaises(TypeError):
      Helper(Recorder(), None)
    with self.assertRaises(TypeError):
      Helper(Recorder(), 'the terminal')

  def test_its_agent_is_the_one_it_was_made_with(self) -> None:
    recorder = Recorder()
    helper = Helper(recorder, self.said.append)
    self.assertIs(recorder, helper.agent)
    self.assertIsInstance(helper.traveller, Traveller)
    self.assertIs(recorder, helper.traveller.agent)

  def test_to_go_is_a_trip_however_far(self) -> None:
    #  beyond a wall wider than a look, where walkTo alone stops
    goal = Vec3(4.5, GROUND, 24.5)
    agent = GridAgent(arena(40, 30) | wall(0, 14, 33, 14),
                      Vec3(4.5, GROUND, 4.5))
    action = Action(Verb.GO, place=goal)
    outcome = Helper(agent, self.said.append).follow(action)
    self.assertTrue(outcome.done)
    self.assertEqual(goal, agent.pos)
    self.assertEqual(goal, outcome.value.pos)
    self.assertEqual(['done: go to (4.50, 4.00, 24.50): at (4.50, 4.00, '
                      '24.50)'], self.said)

  def test_to_go_where_there_is_no_way_is_not_done(self) -> None:
    #  the goal walled in
    world = (arena(20, 20) | wall(8, 13, 12, 13) | wall(8, 17, 12, 17) |
             wall(8, 13, 8, 17) | wall(12, 13, 12, 17))
    agent = GridAgent(world, Vec3(10.5, GROUND, 2.5))
    outcome = Helper(agent, self.said.append).follow(
      Action(Verb.GO, place=Vec3(10.5, GROUND, 15.5)))
    self.assertFalse(outcome.done)
    self.assertEqual('travel', outcome.error.step)
    self.assertTrue(self.said[0].startswith(
      'not done: go to (10.50, 4.00, 15.50): travel: no way to (10.50, '
      '4.00, 15.50)'), self.said[0])

  def test_a_tick_budget_goes_with_the_trip(self) -> None:
    agent = GridAgent(arena(12, 40), Vec3(6.5, GROUND, 2.5))
    outcome = Helper(agent, self.said.append).follow(
      Action(Verb.GO, place=Vec3(6.5, GROUND, 36.5), ticks=40))
    self.assertFalse(outcome.done)
    self.assertIn('the tick budget (40) is spent', self.said[0])

  def test_it_remembers_from_one_go_to_the_next(self) -> None:
    agent = GridAgent(arena(12, 40), Vec3(6.5, GROUND, 2.5))
    helper = Helper(agent, self.said.append)
    helper.follow(Action(Verb.GO, place=Vec3(6.5, GROUND, 36.5)))
    seen = helper.traveller.atlas.columns
    self.assertGreater(seen, 0)
    helper.follow(Action(Verb.GO, place=Vec3(6.5, GROUND, 2.5)))
    self.assertEqual(Vec3(6.5, GROUND, 2.5), agent.pos)
    self.assertGreaterEqual(helper.traveller.atlas.columns, seen)

  def test_what_it_must_do_is_followed_and_given_back(self) -> None:
    #  the strict manner, a test's (SPEC.md 21.19 S2)
    recorder = Recorder(answers={'use': SEEN})
    outcome = Helper(recorder, self.said.append).must(
      Action(Verb.USE, MCBlocks.Lever, LEVER))
    self.assertTrue(outcome.done)
    self.assertEqual([('use', (LEVER,), {})], recorder.asked)
    self.assertEqual(['done: use MCBlocks.Lever at (5, 4, 7): ' + MET],
                     self.said)

  def test_what_it_must_do_and_cant_is_raised_once_said(self) -> None:
    stopped = TesttimeError('take', None, 'no MCItems.PinkWool in the '
                                          'container (it is empty)')
    recorder = Recorder(stops={'take': stopped})
    with self.assertRaises(TesttimeError) as raised:
      Helper(recorder, self.said.append).must(
        Action(Verb.TAKE, MCItems.PinkWool))
    self.assertIs(stopped, raised.exception, 'the step\'s own error')
    self.assertEqual(1, len(self.said))
    self.assertTrue(self.said[0].startswith(
      'not done: take MCItems.PinkWool: '))

  def test_several_it_must_do_are_a_series(self) -> None:
    recorder = Recorder(answers={'open': Container(slots=(WOOL,)),
                                 'take': WOOL})
    outcome = Helper(recorder, self.said.append).must(
      Action(Verb.OPEN, MCBlocks.Chest, CHEST),
      Action(Verb.TAKE, MCItems.PinkWool), Action(Verb.CLOSE))
    self.assertEqual(['open', 'take', 'close'],
                     [step for step, _, _ in recorder.asked])
    self.assertEqual(3, len(outcome.instruction.steps))
    self.assertEqual('done: 3 steps', self.said[-1])

  def test_a_series_it_must_do_stops_at_the_step_it_cant(self) -> None:
    stopped = TesttimeError('take', None, 'it is empty')
    recorder = Recorder(answers={'open': Container(slots=())},
                        stops={'take': stopped})
    with self.assertRaises(TesttimeError) as raised:
      Helper(recorder, self.said.append).must(
        Action(Verb.OPEN, MCBlocks.Chest, CHEST),
        Action(Verb.TAKE, MCItems.PinkWool), Action(Verb.CLOSE))
    self.assertIs(stopped, raised.exception)
    self.assertEqual(['open', 'take'],
                     [step for step, _, _ in recorder.asked])

  def test_it_must_do_something(self) -> None:
    with self.assertRaises(TypeError):
      Helper(Recorder(), self.said.append).must()
    with self.assertRaises(TypeError):
      Helper(Recorder(), self.said.append).must('close')


if __name__ == '__main__':
  unittest.main()
