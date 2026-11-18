#!/usr/bin/env python3
"""
meantwell's own watcher (SPEC.md 21.12): the game runs a session here
asks for, made in the person's own session (their display), since a
session here can't open a game. It is unittas's watcher (unittas.watcher)
on a queue of meantwell's own, so it never shares one with unitTAS's.

  python meantwell_watch.py     (on the Python that has unittas)

- meantwell-queue/request: one line, 'unittas run's arguments (the
  tests): a run to make on the practice instance (unittas.toml). Once it
  is taken, meantwell-queue/run holds the run's results folder, and
  meantwell-queue/done its exit code when it ends.
- One run at a time: a request waits while a run goes.
- A run is watched: where a fixed limit would decide the game is stuck,
  alarm.txt in its results asks, and decision.txt answers (wait, fail or
  abort).

Ctrl+C stops it.

- watcher(root): the watcher of a folder.
- main(): the command; its exit code.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, Optional, TextIO

#  The repository's folder: the runs are made from it, on its unittas.toml
ROOT = os.path.dirname(os.path.abspath(__file__))
#  The queue's folder in it: meantwell's own, never unitTAS's
QUEUE = 'meantwell-queue'


def watcher(root: str, runner: Optional[Callable] = None,
            out: Optional[TextIO] = None,
            environ: Optional[dict] = None) -> Any:
  """
  The watcher of 'root' on its meantwell-queue folder, the package's
  source (src) first on the path of the runs it makes. 'runner', 'out'
  and 'environ' are unittas's QueueWatcher's (a test bench's stand-ins).
  """
  from unittas.watcher import QueueWatcher
  environ = dict(os.environ if environ is None else environ)
  path = [os.path.join(root, 'src')]
  if environ.get('PYTHONPATH'):
    path.append(environ['PYTHONPATH'])
  environ['PYTHONPATH'] = os.pathsep.join(path)
  given = {} if runner is None else {'runner': runner}
  return QueueWatcher(root, queue=os.path.join(root, QUEUE), out=out,
                      environ=environ, **given)


def main() -> int:
  """The command: the watcher of this repository, until Ctrl+C."""
  try:
    import unittas
  except ImportError:
    print('meantwell_watch: %s has no unittas. Run it on the Python that '
          'has (meantwell_env\'s).' % sys.executable, file=sys.stderr)
    return 2
  print('meantwell\'s watcher, on unittas %s: one line of tests in %s is a '
        'run on %s' % (unittas.__version__, os.path.join(QUEUE, 'request'),
                       os.path.join(ROOT, 'unittas.toml')), flush=True)
  return watcher(ROOT).serve()


if __name__ == '__main__':
  sys.exit(main())
