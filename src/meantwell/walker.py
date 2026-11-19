"""
Walker: a walk as a player walks (SPEC.md 21.23). The agent's own walkTo
is a test's step: it sets its look at the next waypoint in one jump,
walks from one block's middle to the next and ends in a sneak and a row
of taps. The walker goes the same way, and

- steers at a point ahead on the way, so a turn begins before its
  corner and the track is a curve: the furthest such point it can walk
  straight to on the way's ground, so that a corner is cut only where
  what the way went round isn't in the cut;
- turns its head by the mouse, a rate each tick, never set outright;
- steers every tick, on the bearing each rate is answered with;
- walks only where it looks, and only while the ticks it is bound to
  would keep it on the ground the way goes on;
- stops by letting go where its own motion carries it there, with a
  tap after it when it stopped short.

It asks a player's means and no others: perceive, keyDown, keyUp,
ticks, and the mouse's (look, toward, ahead, rest and its bearing). Its
way is the terrain's, read
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
  #  How far its middle keeps from a column that isn't the way's ground;
  #  and, once nearer than that, how far it may go to be out of it
  MARGIN, OUT = 0.2, 0.3
  #  How it looks as it walks: this far down, in degrees
  DOWN = 8.0
  #  The ticks of forward it is bound to once it holds it, before a
  #  letting go can be in force: the request that turns, and the request
  #  that lets go
  BOUND = 2
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
    for name in ('toward', 'ahead', 'rest'):
      if not callable(getattr(body, name, None)):
        infoSpec = """a walker turns by the mouse: its body is a Mouse,
        with '%s', not %r"""
        raise TypeError(' '.join((infoSpec % (name, body)).split()))
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
      self._along(seen, way, ground, within, last)
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

  def _keeps(self, ground: set, x: float, z: float, track: list) -> bool:
    """
    Whether the places of 'track', gone to from (x, z), keep it on the
    way's ground. Standing nearer than MARGIN to what isn't that ground
    (an answer came late, and it went a tick further than it reckoned),
    a track that brings it out is kept to from OUT blocks on.
    """
    free = 0.0 if self._on(ground, x, z) else self.OUT
    return self._on(ground, *track[-1]) and all(
      self._on(ground, *each) for each in track
      if math.hypot(each[0] - x, each[1] - z) > free)

  def _straight(self, ground: set, x: float, z: float,
                aim: tuple) -> bool:
    """Whether the straight line from (x, z) to 'aim' keeps it on the
    way's ground, each tenth of a block of it."""
    far = math.hypot(aim[0] - x, aim[1] - z)
    parts = max(1, int(math.ceil(far / 0.1)))
    return self._keeps(ground, x, z, [
      (x + (aim[0] - x) * part / parts, z + (aim[1] - z) * part / parts)
      for part in range(1, parts + 1)])

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

  def letGo(self) -> None:
    """Every key it holds, let go, and the mouse at rest."""
    Routine.letGo(self)
    self.body.rest()

  def _along(self, at: Any, way: tuple, ground: set, within: float,
             last: int) -> None:
    """
    The walk along the way, to where it lets go: steering at a point
    ahead, its feet going while its look is near the way's and the
    ticks it is bound to keep it on the ground. 'at' is its bearing to
    begin with (what it perceived); from then on each tick's is the
    mouse's.
    """
    whole, since, stuck = pace.length(way), 0.0, 0
    place = way[-1]
    while True:
      self.__now__ = at.tick
      self._spent(at, last, place)
      x, z = at.pos.x, at.pos.z
      since, _ = pace.abreast(way, x, z, since)
      short = math.hypot(place[0] - x, place[1] - z)
      going = self.holds('key.forward')
      if not going and short <= max(within, self.NEAR):
        return
      now = at.look.yaw
      if going and whole - since <= self.AHEAD:
        #  where it comes to rest, let go now or a tick on: the letting
        #  go itself is a tick of forward
        misses = [math.hypot(place[0] - rest[0], place[1] - rest[1])
                  for rest in (self._rest(at, [now] * held)[-1]
                               for held in (1, 2))]
        if misses[0] <= misses[1]:
          return
      #  the furthest point ahead it can walk straight to from here on
      #  the way's ground, as it moves now and were it looking there;
      #  failing every one, the way itself, abreast of it. Its feet go
      #  when it nearly looks there and the ticks it is bound to, on the
      #  looks it will have, keep it on that ground
      go, wanted = False, now
      for ahead in (self.AHEAD,) + self.NEARER + (0.0,):
        aim = pace.point(way, since + ahead)
        if math.hypot(aim[0] - x, aim[1] - z) < self.LEAST:
          continue
        wanted = pace.bearing(x, z, *aim)
        if self._straight(ground, x, z, aim) and self._keeps(
            ground, x, z, self._rest(at, [wanted] * self.BOUND)):
          yaws = [look[0] for look in self.body.ahead(
            wanted, self.DOWN, self.BOUND)]
          go = (abs(pace.turned(now, wanted)) <= self.WIDE and
                self._keeps(ground, x, z, self._rest(at, yaws)))
          break
      if go or going:
        stuck = 0
      elif abs(pace.turned(now, wanted)) <= self.body.SMALL:
        stuck += 1
        if stuck > self.STUCK:
          infoSpec = """no step keeps it on the way's ground, %.2f blocks
          short, at (%.2f, %.2f, %.2f)"""
          info = infoSpec % (short, x, at.pos.y, z)
          raise TesttimeError('walk', at, ' '.join(info.split()))
      self._hold('key.forward', go)
      self.body.toward(wanted, self.DOWN)
      at = self.body.bearing

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
