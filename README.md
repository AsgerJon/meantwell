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

- **Not yet:** it has played no game of its own. So far the helper is tested on an agent that only records what it
  is asked. The helper alone in a world, with instructions typed in a terminal, comes next.

## Its tests

```
python -m unittest discover -s tests/unit
```

They need no game. `pip install -e .` brings what they need: worktoy, mcdex and unittas.

## License

Apache-2.0.
