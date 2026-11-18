"""
meantwell's ties to unitTAS (SPEC.md 21.3, 21.6), read from its source:
it never holds a game. Its modules take unittas's values (the
perception among them), its errors and its rules for the ground
(terrain), and the agent as a type only (under TYPE_CHECKING); never the
game's face (api), the run or a test case.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import ast
import os
import unittest

from test_ground import ROOT

SOURCE = os.path.join(ROOT, 'src', 'meantwell')
#  what a module of meantwell may import of unittas as it runs, and what
#  more as a type only
RUNNING = {'unittas.errors', 'unittas.values', 'unittas.perception',
           'unittas.nearblock', 'unittas.terrain'}
TYPES = {'unittas.agent'}


def _typeOnly(node: ast.AST) -> bool:
  """Whether the statement is an 'if TYPE_CHECKING:' block."""
  return (isinstance(node, ast.If) and isinstance(node.test, ast.Name) and
          node.test.id == 'TYPE_CHECKING')


def _imports(tree: ast.AST, typed: bool = False) -> list:
  """(module, whether as a type only) for each import in the tree."""
  found = []
  for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.Import):
      found += [(each.name, typed) for each in node.names]
    elif isinstance(node, ast.ImportFrom):
      found.append((node.module or '', typed))
    else:
      found += _imports(node, typed or _typeOnly(node))
  return found


class TiesTests(unittest.TestCase):

  def test_only_the_values_the_errors_and_the_agent_as_a_type(self) -> None:
    read = 0
    for name in sorted(os.listdir(SOURCE)):
      if not name.endswith('.py'):
        continue
      with open(os.path.join(SOURCE, name), encoding='utf-8') as file:
        tree = ast.parse(file.read())
      read += 1
      for module, typed in _imports(tree):
        if module != 'unittas' and not module.startswith('unittas.'):
          continue
        allowed = RUNNING | TYPES if typed else RUNNING
        self.assertIn(module, allowed, '%s imports %s%s' % (
          name, module, ' as a type' if typed else ''))
    self.assertGreater(read, 1, 'the package was read')

  def test_the_check_sees_an_import_wherever_it_is(self) -> None:
    tree = ast.parse('\n'.join((
      'from typing import TYPE_CHECKING',
      'if TYPE_CHECKING:',
      '  from unittas.agent import Agent',
      'def late():',
      '  from unittas.run import Run',
      '  import unittas.api')))
    self.assertEqual([('typing', False), ('unittas.agent', True),
                      ('unittas.run', False), ('unittas.api', False)],
                     _imports(tree))


if __name__ == '__main__':
  unittest.main()
