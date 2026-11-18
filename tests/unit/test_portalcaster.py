"""
The caster playing a move on a body (SPEC.md 21.21; portalcaster.py),
without a game, on a body that shows what it is told to (castbody.py).
Each move is made by a player's means and checked by them: the hotbar's
key for what it uses, the look turned to the face, the click made only
with the crosshair on that face, the bucket empty after a pour and full
after a scoop. To stand and to dig are the agent's own steps. What can't
be done is said, naming the move.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import unittest

from castagent import CastAgent
from castbody import CastBody
from meantwell.castdoes import CastDoes
from meantwell.castmove import CastMove
from meantwell.portalcaster import PortalCaster
from unittas.errors import TesttimeError
from unittas.nearblock import NearBlock
from unittas.target import Target
from unittas.values import BlockPos, Vec3

EYE = Vec3(11.5, 65.62, 21.5)
GROUND = BlockPos(11, 62, 20)
HOTBAR = {0: 'minecraft:water_bucket', 1: 'minecraft:flint_and_steel',
          2: 'minecraft:dirt', 3: 'minecraft:iron_pickaxe'}


def on(pos: BlockPos, face: str) -> Target:
  return Target(kind='block', pos=pos, face=face, id='minecraft:dirt')


class PortalCasterTests(unittest.TestCase):

  def caster(self, **body) -> tuple:
    """(caster, its body, its agent), the hotbar as the task gives it."""
    made = CastBody(EYE, dict(HOTBAR), **body)
    agent = CastAgent(made)
    self.said = []
    return PortalCaster(agent, self.said.append), made, agent

  def test_dirt_is_put_by_a_click_on_the_face(self) -> None:
    above = BlockPos(11, 63, 20)
    caster, body, _ = self.caster(
      aim=lambda yaw, pitch: on(GROUND, 'up'),
      onUse=lambda made: setattr(made, 'target', on(above, 'south')))
    caster.play(CastMove(CastDoes.DIRT, GROUND, 'up'))
    self.assertEqual([('key.hotbar.3',), ('key.use',)], body.named('tap'))
    (yaw, pitch), = body.named('look')
    #  the face's middle, just inside it: straight north of the eye
    self.assertAlmostEqual(180.0, abs(yaw))
    self.assertAlmostEqual(math.degrees(math.atan2(65.62 - 62.95, 1.0)),
                           pitch)

  def test_no_click_with_the_crosshair_elsewhere(self) -> None:
    caster, body, _ = self.caster(
      aim=lambda yaw, pitch: on(BlockPos(11, 63, 21), 'up'))
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.DIRT, GROUND, 'up'))
    self.assertEqual('cast', stopped.exception.step)
    said = str(stopped.exception)
    self.assertIn('put dirt on the up face of the block at (11, 62, 20)',
                  said)
    self.assertIn('(11, 63, 21)', said)
    self.assertNotIn(('key.use',), body.named('tap'))

  def test_dirt_that_didnt_land_is_said(self) -> None:
    caster, body, _ = self.caster(aim=lambda yaw, pitch: on(GROUND, 'up'))
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.DIRT, GROUND, 'up'))
    self.assertIn('placed nothing', str(stopped.exception))

  def test_a_face_out_of_reach_is_said_before_it_looks(self) -> None:
    caster, body, _ = self.caster()
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.DIRT, BlockPos(11, 62, 14), 'up'))
    self.assertIn('out of reach', str(stopped.exception))
    self.assertEqual([], body.named('look'))

  def test_a_pour_empties_the_bucket(self) -> None:
    caster, body, _ = self.caster(
      aim=lambda yaw, pitch: on(GROUND, 'up'),
      onUse=lambda made: made.put(0, 'minecraft:bucket'))
    caster.play(CastMove(CastDoes.POUR_WATER, GROUND, 'up'))
    self.assertEqual([('key.use',)], body.named('tap'), 'slot 1 is held')

  def test_a_pour_that_left_the_bucket_full_is_said(self) -> None:
    caster, body, _ = self.caster(aim=lambda yaw, pitch: on(GROUND, 'up'))
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.POUR_WATER, GROUND, 'up'))
    self.assertIn('still', str(stopped.exception))

  def test_a_pour_needs_the_bucket_to_hold_it(self) -> None:
    caster, body, _ = self.caster(aim=lambda yaw, pitch: on(GROUND, 'up'))
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.POUR_LAVA, GROUND, 'up'))
    self.assertIn('MCItems.WaterBucket', str(stopped.exception))
    self.assertEqual([], body.named('look'))

  def test_a_scoop_fills_the_bucket(self) -> None:
    cell = BlockPos(10, 63, 21)
    caster, body, _ = self.caster(
      onUse=lambda made: made.put(0, 'minecraft:water_bucket'))
    body.put(0, 'minecraft:bucket')
    caster.play(CastMove(CastDoes.SCOOP_WATER, cell))
    (yaw, pitch), = body.named('look')
    #  the cell's middle: west of the eye, and down
    self.assertAlmostEqual(90.0, yaw)
    self.assertAlmostEqual(math.degrees(math.atan2(65.62 - 63.5, 1.0)),
                           pitch)
    self.assertEqual([('key.use',)], body.named('tap'))

  def test_a_scoop_that_took_nothing_is_said(self) -> None:
    caster, body, _ = self.caster()
    body.put(0, 'minecraft:bucket')
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.SCOOP_WATER, BlockPos(10, 63, 21)))
    self.assertIn('MCItems.Bucket', str(stopped.exception))

  def test_lava_is_fetched_from_the_nearest_source(self) -> None:
    lake = Vec3(12.5, 64.0, 26.5)
    near, far = BlockPos(12, 63, 28), BlockPos(12, 63, 30)
    running = BlockPos(12, 63, 27)
    blocks = (
      NearBlock(pos=far, id='minecraft:lava', liquid=True,
                state=(('level', '0'),)),
      NearBlock(pos=running, id='minecraft:lava', liquid=True,
                state=(('level', '2'),)),
      NearBlock(pos=near, id='minecraft:lava', liquid=True,
                state=(('level', '0'),)),
      NearBlock(pos=BlockPos(12, 63, 26), id='minecraft:grass_block'))
    caster, body, agent = self.caster(
      blocks=blocks, onUse=lambda made: made.put(0, 'minecraft:lava_bucket'))
    body.put(0, 'minecraft:bucket')
    caster.lake = lake
    caster.play(CastMove(CastDoes.FETCH_LAVA))
    self.assertEqual([('walkTo', (lake, 0.25))], agent.asked)
    (yaw, pitch), = body.named('look')
    #  the near source's middle: south of the eye, 2 blocks off
    self.assertAlmostEqual(0.0, yaw)
    self.assertAlmostEqual(math.degrees(math.atan2(65.62 - 63.5, 2.0)),
                           pitch)

  def test_no_lava_in_reach_is_said(self) -> None:
    caster, body, _ = self.caster()
    body.put(0, 'minecraft:bucket')
    caster.lake = Vec3(12.5, 64.0, 26.5)
    with self.assertRaises(TesttimeError) as stopped:
      caster.play(CastMove(CastDoes.FETCH_LAVA))
    self.assertIn('no lava source', str(stopped.exception))

  def test_to_stand_and_to_dig_are_the_agents_own_steps(self) -> None:
    caster, body, agent = self.caster()
    spot = Vec3(11.5, 66.0, 22.5)
    caster.play(CastMove(CastDoes.STAND, spot=spot))
    caster.play(CastMove(CastDoes.DIG, GROUND))
    self.assertEqual([('walkTo', (spot, 0.25)), ('breakBlock', (GROUND,))],
                     agent.asked)

  def test_the_cast_stops_at_the_move_it_cant_make(self) -> None:
    #  the first click of the plan finds the crosshair elsewhere
    caster, body, agent = self.caster(
      aim=lambda yaw, pitch: on(BlockPos(0, 0, 0), 'up'))
    with self.assertRaises(TesttimeError) as stopped:
      caster.cast(BlockPos(10, 64, 20), Vec3(12.5, 64.0, 26.5))
    self.assertIn('move 13 of 78', str(stopped.exception))
    self.assertEqual(12, len(self.said), 'each move made was said')
    self.assertTrue(self.said[0].startswith('move 1 of 78: stand at'))
    self.assertTrue(self.said[1].startswith('move 2 of 78: dig the'))


if __name__ == '__main__':
  unittest.main()
