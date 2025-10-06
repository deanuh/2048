# 2048
2048-Tiny (Turn-Based) in python

## What this is
- **Board**: 4×4 grid of integers (0 = empty).
- **Moves**: slides tiles fully in the chosen direction (W/A/S/D or arrow keys).
- **Merge rule**: equal adjacent tiles merge **once per move** into their sum; a merged tile cannot merge again during the same move.
- **Spawning**: after every **successful** move (board changed), exactly one tile spawns on a random empty cell: **2 with 90%** probability, **4 with 10%**.
- **Scoring**: increases by the **sum of newly created merged tiles** in that move.
- **End condition**: game over when there are **no empty cells and no adjacent equal tiles** in any direction.
- **Restart**: returns to a new board with exactly two starting tiles.
- **Determinism**: `--seed <int>` locks the RNG for reproducible runs.

---

## How to run

> Tested with **Python 3.13** (also works on 3.10+). No external dependencies.

```bash
# check python version
python3 --version

# play normally
python3 main.py

# play deterministically (example seed)
python3 main.py --seed 42

# disable ANSI colors if your terminal renders oddly
python3 main.py --no-color
```
## Controls:

- W / A / S / D — Up / Left / Down / Right
- Arrow keys — also supported
- r — Restart (new game with two starting tiles)
- q — Quit

## What I learned (short):

- Separating game mechanics (slide/merge) from I/O (render/input) made the code easier to test and reason about.
- Enforcing single-merge-per-move is most reliable with the compact → merge-once → pad pattern.
- Injecting a seeded RNG (--seed) made debugging and grading reproducible across machines.
