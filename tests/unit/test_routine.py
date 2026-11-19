"""
What the routines share (SPEC.md 21.15; routine.py), without a game, on
a body that keeps what it is asked (lookbody.py): a press of a key is
the key down and the key up, two requests and no more, which is a tick
less than the body's own tap takes in the game (SPEC.md 21.24).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest

from lookbody import LookBody
from meantwell.routine import Routine


class RoutineTests(unittest.TestCase):

  def test_a_press_is_the_key_down_and_up(self) -> None:
    body = LookBody()
    routine = Routine(body)
    routine.press('key.use')
    self.assertEqual([('keyDown', ('key.use',)), ('keyUp', ('key.use',))],
                     body.asked)
    self.assertEqual(2, body.tick)
    self.assertFalse(routine.holds('key.use'))

  def test_a_key_it_holds_is_let_go_and_pressed_anew(self) -> None:
    #  a press is a press: held down already, it wouldn't be one
    body = LookBody()
    routine = Routine(body)
    routine._hold('key.use', True)
    routine.press('key.use')
    self.assertEqual(['keyDown', 'keyUp', 'keyDown', 'keyUp'],
                     [name for name, _ in body.asked])
    self.assertFalse(routine.holds('key.use'))


if __name__ == '__main__':
  unittest.main()
