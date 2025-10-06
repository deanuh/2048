"""
2048‑Tiny (Turn‑Based)

Meets HW1 acceptance criteria:
- 4x4 grid; controls: WASD (arrows optional via sequences), Restart (r), Quit (q)
- Deterministic slide/merge rules; single merge per move; only spawn after a successful move
- New tile 2 (90%) or 4 (10%) on a random empty square
- Score increases by merged tile value; visible during play
- Game over when no moves remain; restart creates fresh board with two starting tiles
- Determinism hook: --seed <int>; RESTART keeps same RNG stream for reproducibility

Run:
    python3 main.py                # play normally
    python3 main.py --seed 123     # deterministic run
    python3 main.py --no-color # disable ANSI colors in the grid

Python: 3.13
No external dependencies.
"""
from __future__ import annotations
import argparse
import os
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple

# Basic ANSI sequences for terminal styling. Colors are optional and can be
# disabled with --no-color, if you run on windows.  
# padding/width always compoputed using plain text first and then wrap color, so alignment doesnt mess up.

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

# per‑value foreground colors to make larger tiles pop. 
# doesnt affect the cell width
FG = {
    0: "\x1b[38;5;246m",
    2: "\x1b[38;5;250m",
    4: "\x1b[38;5;248m",
    8: "\x1b[38;5;214m",
    16: "\x1b[38;5;208m",
    32: "\x1b[38;5;202m",
    64: "\x1b[38;5;196m",
    128: "\x1b[38;5;33m",
    256: "\x1b[38;5;39m",
    512: "\x1b[38;5;75m",
    1024: "\x1b[38;5;141m",
    2048: "\x1b[38;5;201m",
}


@dataclass
class MoveResult:
    """Return type for Board.move: whether anything moved and the score gained."""
    moved: bool
    score_gain: int


class Board:
    """ Encapsulates the game state and mechanics for a 4×4 2048 board.
        Attributes:
        rng: random.Random used for deterministic spawns when seeded
        grid: 4×4 list of ints (0 = empty)
        score: cumulative score (sum of all merge results so far)
    """
    SIZE = 4

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.grid: List[List[int]] = [[0] * Board.SIZE for _ in range(Board.SIZE)]
        self.score = 0
        self._spawn_random_tile()
        self._spawn_random_tile()


    def move(self, direction: str) -> MoveResult:
        """Apply a move in one of 'w','a','s','d' (up/left/down/right).

        Implementation follows the compact then merge‑once then pad pattern to enforce
        the single‑merge‑per‑move rule:
        1) Extract a line (row or column) in the move direction
        2) Remove zeros (compact)
        3) Scan left‑to‑right once; when two equal tiles meet, merge into their
        sum and skip the next value so it cannot merge again in this move
        4) Pad with zeros to SIZE
        """
        direction = direction.lower()
        if direction not in ("w", "a", "s", "d"):
            return MoveResult(False, 0)

        before = [row[:] for row in self.grid]
        score_gain = 0

        # helpers to read a line (row/col) in move order and to write it back
        def line(idx: int) -> List[int]:
            if direction == "a":
                return self.grid[idx][:]
            if direction == "d":
                return list(reversed(self.grid[idx]))
            if direction == "w":
                return [self.grid[r][idx] for r in range(Board.SIZE)]
            # down
            return [self.grid[r][idx] for r in reversed(range(Board.SIZE))]

        def write_line(idx: int, vals: List[int]):
            if direction == "a":
                self.grid[idx] = vals
            elif direction == "d":
                self.grid[idx] = list(reversed(vals))
            elif direction == "w":
                for r, v in enumerate(vals):
                    self.grid[r][idx] = v
            else:  # down
                for r, v in enumerate(vals):
                    self.grid[Board.SIZE - 1 - r][idx] = v
        # process each row/column independently in the chosen orientation
        for i in range(Board.SIZE):
            arr = line(i)
            compact = [x for x in arr if x != 0]
            merged: List[int] = []
            skip = False
            j = 0
            while j < len(compact):
                # if the next value exists and equals the current, merge once
                if j + 1 < len(compact) and compact[j] == compact[j + 1]:
                    val = compact[j] * 2
                    merged.append(val)
                    score_gain += val # scoring = sum of newly created merged tiles
                    j += 2  # consume pair; merged tile cannot merge again this move
                else:
                    merged.append(compact[j])
                    j += 1
            # pad with zeros to maintain fixed size.
            merged += [0] * (Board.SIZE - len(merged))
            write_line(i, merged)

        moved = self.grid != before
        if moved:
            self.score += score_gain
            self._spawn_random_tile()
        return MoveResult(moved, score_gain)

    def has_moves(self) -> bool:
        """True if an empty exists **or** any adjacent equals exist.
        Used for game‑over detection. """
        if any(0 in row for row in self.grid):
            return True
        # checks right/down neighbors only aka covers all adjacencies once 
        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                v = self.grid[r][c]
                if r + 1 < Board.SIZE and self.grid[r + 1][c] == v:
                    return True
                if c + 1 < Board.SIZE and self.grid[r][c + 1] == v:
                    return True
        return False

    def restart(self):
        """Reset to a fresh game: clear state, zero score, spawn two tiles."""
        self.grid = [[0] * Board.SIZE for _ in range(Board.SIZE)]
        self.score = 0
        self._spawn_random_tile()
        self._spawn_random_tile()

    def _spawn_random_tile(self):
        """Place a 2 (90%) or 4 (10%) on a uniformly random empty cell.
        If no empties remain, do nothing.
        """
        empties: List[Tuple[int, int]] = [
            (r, c) for r in range(Board.SIZE) for c in range(Board.SIZE) if self.grid[r][c] == 0
        ]
        if not empties:
            return
        r, c = self.rng.choice(empties)
        # 90%: 2, 10%: 4
        self.grid[r][c] = 4 if self.rng.random() < 0.10 else 2

    def render(self, use_color: bool = True) -> str:
        """Return a monospace grid with consistent cell widths.
        We compute cell width from the widest numeric value currently on the
        board and center the plain text inside each cell. Colors (if enabled)
        are applied after padding so ANSI codes do not break alignment.
        """
        # determine the widest number (for consistent cell width)
        max_val = max(max(row) for row in self.grid)
        cell_width = max(len(str(max_val)), 4)  # minimum 4 spaces wide

        # Build horizontal border once; reused per row
        hbar = "+" + "+".join(["-" * cell_width] * Board.SIZE) + "+"

        lines = [hbar]
        for r in range(Board.SIZE):
            row_cells = []
            for c in range(Board.SIZE):
                v = self.grid[r][c]
                s_plain = "" if v == 0 else str(v)

                # pad/center using plain text first
                cell = s_plain.center(cell_width)

                # then wrap in color (doesn't affect spacing)
                if use_color and v in FG and s_plain:
                    cell = FG[v] + cell + RESET

                row_cells.append(cell)
            lines.append("|" + "|".join(row_cells) + "|")
            lines.append(hbar)

        # <-- make sure this return is OUTSIDE the for-loop
        return "\n".join(lines)




ARROW_PREFIX = "\x1b["
# Map ANSI arrow codes to WASD equivalents: up, down, right, left
ARROWS = {"A": "w", "B": "s", "C": "d", "D": "a"}  # up,down,right,left


def read_command() -> str:
    """Read a single command from stdin. Supports WASD, r, q, and ANSI arrows.
    Returns lowercase char or empty string on invalid input.
    """
    try:
        ch = sys.stdin.read(1)
    except KeyboardInterrupt:
        return "q"
    if ch == "\x1b":  # possible arrow
        nxt = sys.stdin.read(1)
        if nxt == "[":
            code = sys.stdin.read(1)
            return ARROWS.get(code, "")
        return ""
    return ch.lower()


# GAME LOOP

def clear_screen():
    """Best‑effort terminal clear on Windows/*nix."""
    os.system("cls" if os.name == "nt" else "clear")


def play(seed: int | None, use_color: bool):
    """Top‑level turn loop: render → input → apply rules → (maybe) spawn → next.
    The RNG is seeded once up front. Restart reuses the same RNG stream so that
    behavior stays deterministic within a single run when `--seed` is provided.
    """
    rng = random.Random(seed)
    board = Board(rng)

    while True:
        clear_screen()
        print(f"{BOLD if use_color else ''}2048 — Tiny (Turn‑Based){RESET if use_color else ''}")
        print("Controls: WASD or arrows = move • r = restart • q = quit")
        if seed is not None:
            print(f"Deterministic mode seed = {seed}")
        print()
        print(board.render(use_color))
        print(f"Score: {board.score}")

        # End‑state: no empties and no adjacent equals
        if not board.has_moves():
            print(BOLD + "\nGame over! Press r to restart, q to quit." + (RESET if use_color else ""))
            cmd = read_command()
            if cmd == "r":
                board.restart()
                continue
            if cmd == "q":
                break
            continue

        cmd = read_command()
        if cmd in ("w", "a", "s", "d"):
            result = board.move(cmd)
            # if illegal no change, do nothing 
            continue
        elif cmd == "r":
            board.restart()
            continue
        elif cmd == "q":
            break
        else:
            # ignore unknown input
            continue


def parse_args(argv: List[str]):
    p = argparse.ArgumentParser(description="2048‑Tiny CLI")
    p.add_argument("--seed", type=int, default=None, help="Deterministic RNG seed (int)")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors in the grid")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    try:
        play(args.seed, use_color=not args.no_color)
    except Exception as e:
        # Be explicit to avoid ambiguity during grading; crash ladder transparency
        sys.stderr.write(f"Unexpected error: {e}\n")
        raise

