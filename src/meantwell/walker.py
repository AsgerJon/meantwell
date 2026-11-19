"""
Walker: a walk as a player walks (SPEC.md 21.23). The agent's own walkTo
is a test's step: it sets its look at the next waypoint in one jump,
walks from one block's middle to the next and ends in a sneak and a row
of taps. The walker goes the same way, and

- steers at a point ahead on the way, so a turn begins before its
  corner and the track is a curve;
- turns its head by the mouse, a part of the way each request, never
  set outright;
- walks only where it looks, and only while the ticks it is bound to
  would keep it on the ground the way goes on;
- stops by letting go where its own motion carries it there, with a
  tap after it when it stopped short.

It asks a player's means and no others: perceive, keyDown, keyUp,
ticks, and the mouse's look and toward. Its way is the terrain's, read
from one perception. A way with a door, a ladder, water, a jump or a
drop in it isn't its yet: it says which, and whoever asked may ask the
agent's walkTo for that stretch.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from unittas.errors import TesttimeError
from unittas.terrain import Terrain
from unittas.values import Vec3

from . import pace
from .routine import Routine

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional

  from unittas.perception import Perception


class Walker(Routine):
  """
  The walker of one body, which is a Mouse's (it turns by 'toward').

    walker = Walker(Mouse(game))
    walker.walk(Vec3(4.5, 64.0, -2.5))
    walker.walk(place, facing=Vec3(6.5, 65.0, -2.5))  # and looks there
    walker.way                                    # the way it took last
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  #  How it looks around for its way: blocks across, below, above
  AROUND = (8, 3, 3)
  #  How far ahead on the way it steers at, in blocks; and the shorter
  #  ones it tries when that one's ticks would leave the ground
  AHEAD = 1.5
  NEARER = (1.0, 0.5, 0.25)
  #  How far off the way ahead its look may be for its feet to go, in
  #  degrees: wider off, the head comes round first
  WIDE = 60.0
  #  How far its middle keeps from a column that isn't the way's ground
  MARGIN = 0.2
  #  How it looks as it walks: this far down, in degrees
  DOWN = 8.0
  #  The ticks of forward it is bound to once it holds it, before a
  #  letting go can be in force: a key's request, a look's two, the next
  #  perception, and the request that lets go. And how many of those
  #  pass before a look asked now is in force
  BOUND, LAG = 5, 2
  #  Stopped below this speed, in blocks a tick
  STOPPED = 0.003
  #  The least margin a walk ends within, as the agent's
  LEAST = 0.05
  #  A stop short by less than this is made up sneaking; and how many
  #  taps a stop may take
  SNEAKS, TAPS = 0.15, 3
  #  With its feet not yet going, this near is a tap's
  NEAR = 0.5
  #  How many looks in a row may find no step it can take
  STUCK = 40

  #  Fallback Variables

  #  Private Variables
  __way__: tuple = ()

  #  Public Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def way(self) -> tuple:
    """The way it took last: each (x, z), where it stood first."""
    return self.__way__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: Any) -> None:
    """The walker of 'body': a Mouse, for its toward."""
    if not callable(getattr(body, 'toward', None)):
      infoSpec = """a walker turns by the mouse: its body is a Mouse, with
      'toward', not %r"""
      raise TypeError(' '.join((infoSpec % (body,)).split()))
    Routine.__init__(self, body)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def walk(self, place: Vec3, within: float = 0.25,
           facing: Optional[Vec3] = None,
           ticks: Optional[int] = None) -> Perception:
    """
    Walks to 'place' and stops there: within 'within' blocks across, and
    still; looking at 'facing' then, where one is given. What it
    perceives there.

    Parameters
    ----------
    place : Vec3
      Where to stand: in what one look around shows.
    within : float
      How near is there, across.
    facing : Vec3, optional
      Where to look, once there.
    ticks : int, optional
      The walk's tick budget; 100 and 12 a block of the way, left out.

    Raises
    ------
    TesttimeError
      There is no way to the place in what it sees, the way isn't one
      it walks yet (a door, a ladder, water, a jump, a drop), no step
      keeps it on the way's ground, or the tick budget is spent.
    """
    for name, each in (('place', place), ('facing', facing)):
      if not isinstance(each, Vec3) and (each is not None or
                                         name == 'place'):
        raise TypeError('a walk\'s %s is a Vec3, not %r' % (name, each))
    if within < self.LEAST:
      infoSpec = """a walk's margin is %r: the least it can be sure of is
      %r"""
      raise ValueError(' '.join((infoSpec % (within, self.LEAST)).split()))
    if ticks is not None and ticks <= 0:
      raise ValueError('a tick budget is above 0, not %r' % (ticks,))
    seen = self.body.perceive(*self.AROUND)
    self.__now__ = seen.tick
    terrain = Terrain(seen, *self.AROUND)
    path, whole = terrain.path(seen.pos, place)
    if path is None or not whole:
      infoSpec = """no way to (%.2f, %.2f, %.2f) from (%.2f, %.2f, %.2f)
      in what one look around shows (%d blocks around, %d below, %d
      above)"""
      info = infoSpec % ((place.x, place.y, place.z, seen.pos.x,
                          seen.pos.y, seen.pos.z) + self.AROUND)
      raise TesttimeError('walk', seen, ' '.join(info.split()))
    self._plain(terrain, seen, path)
    way = ((seen.pos.x, seen.pos.z),) + tuple((at.x, at.z) for at in path)
    self.__way__ = way
    ground = self._ground(terrain, seen.pos.y, way)
    if ticks is None:
      ticks = 100 + int(math.ceil(12 * pace.length(way)))
    last = seen.tick + ticks
    try:
      self._along(way, ground, within, last)
      seen = self._settle(way[-1], within, last)
    finally:
      self.letGo()
    if facing is not None:
      eye = seen.eye
      across = math.hypot(facing.x - eye.x, facing.z - eye.z)
      self.body.look(pace.bearing(eye.x, eye.z, facing.x, facing.z),
                     math.degrees(math.atan2(-(facing.y - eye.y), across)))
      seen = self._see()
    return seen

  def _plain(self, terrain: Terrain, seen: Perception, path: list) -> None:
    """TesttimeError unless the way is one it walks: on one level, with
    no door, ladder or water in it."""
    before = seen.pos
    for at in path:
      column = math.floor(at.x), math.floor(at.z)
      what = None
      if terrain.doors(*column):
        what = 'a door'
      elif terrain.ladders(*column):
        what = 'a ladder'
      elif terrain.wet(column[0], column[1], at.y):
        what = 'water'
      elif at.y > before.y + Terrain.STEP:
        what = 'a jump'
      elif at.y < before.y - Terrain.STEP:
        what = 'a drop'
      if what is not None:
        infoSpec = """the way has %s in it, at (%.2f, %.2f, %.2f), and
        the walker doesn't walk that yet"""
        info = infoSpec % (what, at.x, at.y, at.z)
        raise TesttimeError('walk', seen, ' '.join(info.split()))
      before = at

  def _ground(self, terrain: Terrain, level: float, way: tuple) -> set:
    """The columns it may have its middle over: those with a floor at
    its level, and the way's own."""
    (cx, cz), around = (math.floor(way[0][0]), math.floor(way[0][1])), \
      self.AROUND[0]
    ground = set()
    for x in range(cx - around, cx + around + 1):
      for z in range(cz - around, cz + around + 1):
        if any(abs(floor - level) <= Terrain.STEP
               for floor in terrain.floors(x, z)):
          ground.add((x, z))
    whole, along = pace.length(way), 0.0
    while along <= whole:
      x, z = pace.point(way, along)
      ground.add((math.floor(x), math.floor(z)))
      along += 0.25
    return ground

  def _on(self, ground: set, x: float, z: float) -> bool:
    """Whether its middle there keeps MARGIN from every column that
    isn't the way's ground."""
    return all((math.floor(x + dx), math.floor(z + dz)) in ground
               for dx in (-self.MARGIN, self.MARGIN)
               for dz in (-self.MARGIN, self.MARGIN))

  def _rest(self, seen: Perception, yaws: list) -> list:
    """
    Where it is each tick from now, to rest: forward held for a tick
    with each of 'yaws' in turn, then the keys let go. Each (x, z).
    """
    x, z = seen.pos.x, seen.pos.z
    vx, vz = seen.motion.x, seen.motion.z
    track = []
    for yaw in yaws:
      x, z, vx, vz = pace.tick(x, z, vx, vz, *pace.push(yaw, 1, 0))
      track.append((x, z))
    while math.hypot(vx, vz) >= self.STOPPED:
      x, z, vx, vz = pace.tick(x, z, vx, vz, 0.0, 0.0)
      track.append((x, z))
    return track or [(x, z)]

  def _spent(self, seen: Perception, last: int, place: tuple) -> None:
    """TesttimeError when the walk's tick budget is spent."""
    if seen.tick <= last:
      return
    infoSpec = """the tick budget is spent, %.2f blocks short, at (%.2f,
    %.2f, %.2f)"""
    info = infoSpec % (math.hypot(place[0] - seen.pos.x,
                                  place[1] - seen.pos.z), seen.pos.x,
                       seen.pos.y, seen.pos.z)
    raise TesttimeError('walk', seen, ' '.join(info.split()))

  def _along(self, way: tuple, ground: set, within: float,
             last: int) -> None:
    """
    The walk along the way, to where it lets go: steering at a point
    ahead, its feet going while its look is near the way's and the
    ticks it is bound to keep it on the ground.
    """
    whole, since, stuck = pace.length(way), 0.0, 0
    place = way[-1]
    while True:
      seen = self._see()
      self._spent(seen, last, place)
      x, z = seen.pos.x, seen.pos.z
      since, _ = pace.abreast(way, x, z, since)
      short = math.hypot(place[0] - x, place[1] - z)
      going = self.holds('key.forward')
      if not going and short <= max(within, self.NEAR):
        return
      now = seen.look.yaw
      if going and whole - since <= self.AHEAD:
        #  where it comes to rest, let go now or some ticks on: the
        #  letting go itself is a tick of forward
        rests = [self._rest(seen, [now] * (1 + more))[-1]
                 for more in range(self.BOUND)]
        misses = [math.hypot(place[0] - at[0], place[1] - at[1])
                  for at in rests]
        best = misses.index(min(misses))
        if best < self.BOUND - 1:
          if best:
            self.body.ticks(best)
          return
      #  the furthest point ahead it could walk straight at from here,
      #  were it looking there; its feet go when it nearly does, and the
      #  ticks it is bound to, on the look it has by then, keep it on
      #  the ground
      go, wanted = False, None
      for ahead in (self.AHEAD,) + self.NEARER:
        wanted = pace.bearing(x, z, *pace.point(way, since + ahead))
        if all(self._on(ground, *at) for at in self._rest(
            seen, [wanted] * self.BOUND)):
          off = pace.turned(now, wanted)
          soon = now + min(max(off, -self.body.FASTEST), self.body.FASTEST)
          yaws = [now] * self.LAG + [soon] * (self.BOUND - self.LAG)
          go = abs(off) <= self.WIDE and all(
            self._on(ground, *at) for at in self._rest(seen, yaws))
          break
      if go or going:
        stuck = 0
      elif abs(pace.turned(now, wanted)) <= self.body.SMALL:
        stuck += 1
        if stuck > self.STUCK:
          infoSpec = """no step keeps it on the way's ground, %.2f blocks
          short, at (%.2f, %.2f, %.2f)"""
          info = infoSpec % (short, x, seen.pos.y, z)
          raise TesttimeError('walk', seen, ' '.join(info.split()))
      self._hold('key.forward', go)
      self.body.toward(wanted, self.DOWN)

  def _settle(self, place: tuple, within: float, last: int) -> Perception:
    """
    The stop: every key let go, still; and while it stands short by more
    than 'within', a tap towards the place with the key that lies
    nearest that way, sneaking when it is very near.
    """
    for tap in range(self.TAPS + 1):
      self.letGo()
      seen = self._see()
      while math.hypot(seen.motion.x, seen.motion.z) >= self.STOPPED:
        self._spent(seen, last, place)
        seen = self._see()
      short = math.hypot(place[0] - seen.pos.x, place[1] - seen.pos.z)
      if short <= within:
        return seen
      if tap == self.TAPS:
        break
      off = pace.turned(seen.look.yaw, pace.bearing(
        seen.pos.x, seen.pos.z, *place))
      key = ('key.forward', 'key.right', 'key.back',
             'key.left')[int(((off + 45.0) % 360.0) // 90.0)]
      sneak = short < self.SNEAKS
      each = pace.SPEED * (pace.SNEAK if sneak else 1.0)
      held = max(1, int(round(short / each)))
      self._hold('key.sneak', sneak)
      self._hold(key, True)
      if held > 1:
        self.body.ticks(held - 1)
    infoSpec = """%d taps on, it stands %.2f blocks from the place, at
    (%.2f, %.2f, %.2f)"""
    info = infoSpec % (self.TAPS, short, seen.pos.x, seen.pos.y,
                       seen.pos.z)
    raise TesttimeError('walk', seen, ' '.join(info.split()))
