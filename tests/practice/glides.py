"""
The glider's scorecard, and the search of its knobs on it (SPEC.md
21.15, 21.17), without a game: thousands of flights in the model the
practice game confirmed (skybody.py).

An episode is a start in the air (a height, falling as one who walked
off an edge) and a place on the ground (how far, which way), within what
a glide from that height reaches and no nearer than it can come down
straight. Its score is how far from the place the glider came to rest,
in blocks, and 20 more for each block a tick it met the ground faster
than 0.45 (soft is under 0.5). A flight that ended otherwise scores 100.

Two sets of episodes, from two seeds: one the search scores on, one held
back, to check that what it found is the skill and not the scorecard.
The game doesn't wait for the one who asks: with 'late' above 0, that
share of the requests is run a tick late, by a seed of the episode's
own, to check that the skill isn't the stand-in's even ticks.

  PYTHONPATH=src:tests/unit python tests/practice/glides.py score
  PYTHONPATH=src:tests/unit python tests/practice/glides.py score 0.2
  (a fifth of the requests late)
  PYTHONPATH=src:tests/unit python tests/practice/glides.py search 160 6
  (160 sets of knobs tried, on 6 processes)

- episodes(seed, count): a set of episodes.
- score(knobs, episodes, late): each episode's (score, miss, sink).
- search(count, workers): the best knobs found, by random search and
  then by small changes about the best.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import math
import multiprocessing
import random
import sys
from typing import Optional

from meantwell import glide
from meantwell.glider import Glider
from skybody import SkyBody
from unittas.errors import TesttimeError
from unittas.values import Vec3

#  The two sets' seeds, and how many episodes each has
SCORED, HELD_BACK, COUNT = 20261118, 81116202, 48
#  How one who walked off an edge falls as an episode begins
FALLING = Vec3(0.0, -0.1, 0.2)
#  Each knob the search turns, with the least and the most it tries;
#  whole numbers for those that count ticks or looks
KNOBS = {'STEEP': (15.0, 50.0), 'FLARE': (2.0, 20.0),
         'FLARE_PITCH': (-15.0, 15.0), 'HARD': (5.0, 80.0),
         'LOW': (4.0, 40.0), 'HOLD': (1, 6), 'COMMIT': (2, 8)}


def reach(high: float) -> float:
  """How far a glide from 'high' gets at best, by the model: the look
  held 5 down from the fall's first tick."""
  x = y = z = 0.0
  vx, vy, vz = FALLING.x, FALLING.y, FALLING.z
  while y > -high:
    vx, vy, vz = glide.ahead(vx, vy, vz, 0.0, 5.0)
    x, y, z = x + vx, y + vy, z + vz
  return math.hypot(x, z)


def episodes(seed: int, count: int = COUNT) -> list:
  """'count' episodes from 'seed': each (height, across, bearing)."""
  chance = random.Random(seed)
  made = []
  for _ in range(count):
    high = chance.uniform(15.0, 90.0)
    across = chance.uniform(1.2 * high, 0.9 * reach(high))
    made.append((high, across, chance.uniform(-180.0, 180.0)))
  return made


def flown(knobs: dict, episode: tuple, late: float = 0.0) -> tuple:
  """One episode flown with the knobs, the share 'late' of its requests
  run a tick late: (score, miss, sink)."""
  high, across, bearing = episode
  place = Vec3(-math.sin(math.radians(bearing)) * across, 0.0,
               math.cos(math.radians(bearing)) * across)
  chance = random.Random(repr(episode))
  glider = type('Tuned', (Glider,), dict(knobs))(SkyBody(
    Vec3(0.0, high, 0.0), FALLING,
    late=lambda: 1 if chance.random() < late else 0))
  try:
    glider.takeOff()
    glider.glide(place)
  except TesttimeError:
    if glider.miss is None:
      return 100.0, math.inf, math.inf
  return (glider.miss + 20.0 * max(0.0, glider.sink - 0.45), glider.miss,
          glider.sink)


def score(knobs: dict, flights: list, late: float = 0.0) -> list:
  """Each episode's (score, miss, sink), flown with the knobs, the
  share 'late' of the requests run a tick late."""
  return [flown(knobs, each, late) for each in flights]


def summed(scores: list) -> dict:
  """A set's scores in a few numbers."""
  misses = sorted(miss for _, miss, _ in scores)
  return {'mean': sum(each for each, _, _ in scores) / len(scores),
          'within 3': sum(1 for miss in misses if miss <= 3.0),
          'soft': sum(1 for _, _, sink in scores if sink < glide.SOFT),
          'of': len(scores), 'median miss': misses[len(misses) // 2],
          'worst miss': misses[-1],
          'hardest': max(sink for _, _, sink in scores)}


def _mean(knobs: dict) -> float:
  return summed(score(knobs, episodes(SCORED)))['mean']


def _drawn(chance: random.Random, about: Optional[dict] = None) -> dict:
  """Knobs drawn anew; or, 'about' given, two of its knobs moved a
  little."""
  knobs = dict(about or {})
  names = sorted(KNOBS) if about is None else chance.sample(sorted(KNOBS), 2)
  for name in names:
    least, most = KNOBS[name]
    if about is None:
      value = chance.uniform(least, most)
    else:
      value = knobs[name] + chance.gauss(0.0, (most - least) / 8.0)
    value = max(least, min(most, value))
    knobs[name] = int(round(value)) if isinstance(least, int) else round(
      value, 2)
  return knobs


def search(count: int, workers: int = 8, seed: int = 1) -> tuple:
  """
  The best knobs found on the scored set, and their mean score: half of
  'count' drawn anew, then the rest in rounds of small changes about
  the best so far.
  """
  chance = random.Random(seed)
  now = {name: getattr(Glider, name) for name in KNOBS}
  with multiprocessing.Pool(workers) as pool:
    best, least = now, pool.apply(_mean, (now,))
    tried = [_drawn(chance) for _ in range(count // 2)]
    rounds = [tried] + [None] * max(1, (count - len(tried)) // (2 * workers))
    for candidates in rounds:
      if candidates is None:
        candidates = [_drawn(chance, best) for _ in range(2 * workers)]
      for knobs, mean in zip(candidates, pool.map(_mean, candidates)):
        if mean < least:
          best, least = knobs, mean
  return best, least


def main(argv: list) -> int:
  """The command: 'score' the glider as it is (the share of requests
  run late, if given), or 'search' N knobs."""
  now = {name: getattr(Glider, name) for name in KNOBS}
  if argv[:1] == ['score']:
    late = float(argv[1]) if len(argv) > 1 else 0.0
    for name, seed in (('scored', SCORED), ('held back', HELD_BACK)):
      print(name, json.dumps(summed(score(now, episodes(seed), late))))
    return 0
  if argv[:1] == ['search']:
    count = int(argv[1]) if len(argv) > 1 else 160
    workers = int(argv[2]) if len(argv) > 2 else 8
    best, least = search(count, workers)
    print('as it is:', json.dumps(now))
    print('found   :', json.dumps(best), 'mean %.3f' % least)
    for name, seed in (('scored', SCORED), ('held back', HELD_BACK)):
      print(name, 'as it is', json.dumps(summed(score(now, episodes(seed)))))
      print(name, 'found   ', json.dumps(summed(score(best,
                                                      episodes(seed)))))
    return 0
  print(__doc__)
  return 2


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
