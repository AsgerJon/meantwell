# meantwell
This robotic minecraft player tries to help you and follow your instructions. 

## The rules it is built by

- **It is a player and nothing more.** It uses the keys, the mouse's look, clicks, its hotbar and the game's screens,
  as you do. It is never teleported, healed or given anything, and it runs no commands.
- **It says what it did and saw.** When it can't do a step, it says which step, what it did and what it saw. It never
  claims a step it didn't complete.
- **It plays on your own machine, and nowhere else:** alone in a world, or on a server on 127.0.0.1 that you join. It
  has no account, it joins nobody's server, and it never passes for a person.

## Today

- **Its body is [unitTAS](https://github.com/AsgerJon/unitTAS)'s:** the probe inside the real game, on ten ports from
  1.7.10 to 26.3, and the scenario agent, which walks, uses, breaks and places blocks, opens containers, and examines
  and identifies what it sees.
- **meantwell itself has instructions,** each a value, and a helper that follows them on an agent and says what
  came of each: an action (go, use, break, place, open, take, put, close, wait), an examination (its inventory, an
  open container's contents, what a block is by its looks), a series of them, or one that depends on what an
  examination finds.

  ```python
  helper = Helper(agent, print)
  helper.follow(Steps((Action(Verb.OPEN, MCBlocks.Chest, chest),
                       Action(Verb.TAKE, MCItems.PinkWool),
                       Action(Verb.CLOSE))))
  # done: open MCBlocks.Chest at (0, 4, 6): it holds 1 minecraft:wool:6
  # done: take MCItems.PinkWool: 1 minecraft:wool:6 moved
  # done: close
  # done: 3 steps
  ```

- **In a unitTAS test** a series of actions is written in short words, by the scene's own things, with no place
  in numbers. `HelperTestCase` is a scenario's test case with a helper; what it plays is noted line by line under
  the test's line in the report, and a step the robot can't complete is the test's error.

  ```python
  class ChestTests(HelperTestCase):

    def test_the_wool_goes_in(self) -> None:
      chest = self.scene.place(MCBlocks.Chest, at=(0, 0, 6))  # setup, by command
      self.game.setSlot('main.0', MCItems.PinkWool)           # setup too
      self.play(Verb.OPEN(chest), Verb.PUT(MCItems.PinkWool), Verb.CLOSE())
      self.assertIn(MCItems.PinkWool, chest.contents())       # examined by command
  ```

  The same values are followed without a test: `Helper(agent, print).follow(Verb.OPEN(chest))`. Nothing of
  meantwell but that one test case takes unitTAS's testing.
- **Long trips:** `Traveller(agent).travel(place)` goes further than one look shows. It remembers the ground it was
  shown (`Atlas`), goes to the edge of it to look further, and so gets around a wall wider than a look and out of a
  dead end, where the agent's own `walkTo` stops. The helper's `go` is such a trip.
- **Swimming:** `Swimmer(body)` swims to a place as 1.13 has swimming (`swim`): laid level under water, one block
  high, by sprint and its look, through a gap one block high, and out at a bank. It comes up from under water
  (`surface`) and paddles upright at the top (`paddle`), the way every version has. It plays the body by five of a
  player's means: perceive, key down, key up, look, ticks.
- **Gliding:** `Glider(body)` opens an elytra's wings (`takeOff`: one press of jump as it falls, or a forward jump
  first where it stands) and glides to a place (`glide`). It steers by its look alone, choosing its pitch by flying
  the game's own reckoning of an elytra ahead (`glide.py`), and comes down softly, sliding to rest at the place.
- **In a real game** (26.3, the practice instance in `unittas.toml`), by a player's inputs alone:
  - on flat ground the traveller arrived each time where `walkTo` alone stopped, and across natural terrain it
    arrived on five trips of 40 to 82 blocks;
  - the swimmer came up from the bed of a pool three deep, stayed afloat and paddled out; swam it level under
    water from end to end at 0.17 blocks a tick, out at the bank, and through a gap one block high;
  - a series written as above used a lever, put wool in a chest and took it out again, each step said in the
    test's report;
  - the glider, from a tower 40 high, came to rest within 1.8 blocks of places 70 to 200 blocks off on flat
    ground, eight glides of eight, each softly. Its model of the flight stayed within 0.04 blocks of the game's
    over flights of up to 520 ticks.
- **Not yet:** the traveller swimming water it can't see across (it goes round, or says there is no way); a thing
  found by looking; a whole task as one instruction; instructions typed in a terminal; rockets, and a glide to
  ground that isn't flat.

## Its practice runs

`meantwell_watch.py` is meantwell's own watcher: started by a person on the Python that has unittas, it makes the
game runs a session asks for, one at a time, on its own queue (`meantwell-queue/`). A line of tests in
`meantwell-queue/request` is a run of `unittas run` on the practice instance; its report lands in
`unittas-results/`.

## Its tests

```
python -m unittest discover -s tests/unit
```

They need no game. `pip install -e .` brings what they need: worktoy, mcdex and unittas.

## License

Apache-2.0.
