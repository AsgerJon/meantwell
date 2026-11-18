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
- **meantwell itself is its ground so far:** the package and its first tests. Instructions come next, then the helper
  alone in a world.

## Its tests

```
python -m unittest discover -s tests/unit
```

They need no game. They need worktoy, mcdex and unittas installed; unittas comes from unitTAS's own tree (its
`python/` folder), not from an index.

## License

Apache-2.0.
