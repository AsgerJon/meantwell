"""
CastDoes: what a move of a portal cast does (SPEC.md 21.21), each a
thing a player does with its feet, its hands, a bucket, dirt, or a flint
and steel. A closed set.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class CastDoes(KeeNum):
  """What a move does, its value the words it is said by."""
  #  goes to a spot and stands there
  STAND = Kee[str]('stand at')
  #  breaks a block of the ground, or of its own dirt
  DIG = Kee[str]('dig')
  #  puts a block of dirt against a block's face
  DIRT = Kee[str]('put dirt on')
  #  empties its bucket of water, or of lava, against a block's face
  POUR_WATER = Kee[str]('pour water on')
  POUR_LAVA = Kee[str]('pour lava on')
  #  takes a water source up in its empty bucket
  SCOOP_WATER = Kee[str]('scoop the water at')
  #  goes to the lake and takes a lava source up in its empty bucket
  FETCH_LAVA = Kee[str]('fetch lava from the lake')
  #  strikes its flint and steel on a block's face
  LIGHT = Kee[str]('light')
  #  walks into the portal and stands in it
  ENTER = Kee[str]('stand in the portal at')
