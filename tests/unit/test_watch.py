"""
meantwell's own watcher (SPEC.md 21.12; meantwell_watch.py), without a
game: unittas's watcher on a queue of meantwell's own, so it never
shares one with unitTAS's. A request is 'unittas run's arguments, run
from the repository's folder on the Python the watcher runs on, with the
package's source on its path; its results folder is named in the queue
before the run starts, and its exit code when it ends.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import unittest

from test_ground import ROOT

if ROOT not in sys.path:
  sys.path.insert(0, ROOT)

import meantwell_watch  # noqa: E402  (found once the root is on the path)


class WatchTests(unittest.TestCase):

  def setUp(self) -> None:
    self.root = tempfile.mkdtemp(prefix='meantwell-watch-')
    self.addCleanup(shutil.rmtree, self.root, True)
    self.ran = []
    self.out = io.StringIO()

  def runner(self, argv: list, cwd: str, env: dict) -> int:
    self.ran.append((argv, cwd, env))
    return 0

  def watcher(self, environ: dict = None):
    return meantwell_watch.watcher(self.root, runner=self.runner,
                                   out=self.out, environ=environ or {})

  def test_its_queue_is_its_own(self) -> None:
    self.assertEqual('meantwell-queue', meantwell_watch.QUEUE)
    self.assertEqual(os.path.join(self.root, 'meantwell-queue'),
                     self.watcher().queue)
    self.assertEqual(self.root, self.watcher().root)

  def test_a_request_is_a_run_of_unittas_from_the_root(self) -> None:
    watcher = self.watcher()
    os.makedirs(watcher.queue)
    with open(os.path.join(watcher.queue, 'request'), 'w') as file:
      file.write('tests.game.test_trips\n')
    self.assertTrue(watcher.once())
    (argv, cwd, env), = self.ran
    self.assertEqual([sys.executable, '-m', 'unittas', 'run',
                      'tests.game.test_trips', '--watched', '--results'],
                     argv[:-1])
    self.assertEqual(self.root, cwd)
    with open(os.path.join(watcher.queue, 'run')) as file:
      results = file.read().strip()
    self.assertEqual(argv[-1], results)
    self.assertEqual(os.path.join(self.root, 'unittas-results'),
                     os.path.dirname(results))
    with open(os.path.join(watcher.queue, 'done')) as file:
      self.assertEqual('0', file.read().strip())
    self.assertFalse(os.path.exists(os.path.join(watcher.queue, 'request')))
    self.assertFalse(watcher.once(), 'nothing more is waiting')

  def test_the_packages_source_is_on_the_runs_path(self) -> None:
    source = os.path.join(self.root, 'src')
    self.assertEqual(source, self.watcher().environ['PYTHONPATH'])
    kept = self.watcher({'PYTHONPATH': '/somewhere/else'})
    self.assertEqual(source + os.pathsep + '/somewhere/else',
                     kept.environ['PYTHONPATH'])

  def test_the_root_is_the_repositorys_folder(self) -> None:
    self.assertEqual(ROOT, meantwell_watch.ROOT)
    self.assertTrue(os.path.isfile(os.path.join(meantwell_watch.ROOT,
                                                'unittas.toml')))


if __name__ == '__main__':
  unittest.main()
