"""
Simple deterministic tests for manual/automated checks.
Run with:
    python3 test_seed.py

These tests avoid external frameworks for portability.
"""
from main import Board
import random


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"Assertion failed: {a} != {b}. {msg}")


def board_from_rows(rows):
    rng = random.Random(0)
    B = Board(rng)
    B.grid = [r[:] for r in rows]
    B.score = 0
    return B


def test_single_merge_per_move():
    B = board_from_rows([[2,2,2,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]])
    B.move('a')  # left
    assert_eq(B.grid[0], [4,2,0,0], "Single merge per move failed")


def test_no_spawn_on_illegal_move():
    # a left move on an already left‑packed, no‑merge row should not change board
    rng = random.Random(1)
    B = Board(rng)
    B.grid = [[2,4,8,16],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
    before = [row[:] for row in B.grid]
    B.move('a')
    after = [row[:] for row in B.grid]
    assert_eq(after, before, "Illegal move changed board/spawned a tile")


def test_game_over_detection():
    B = board_from_rows([
        [2,4,2,4],
        [4,2,4,2],
        [2,4,2,4],
        [4,2,4,2],
    ])
    assert_eq(B.has_moves(), False, "Game over not detected on full non‑mergeable board")


def test_spawn_probability_shape_only():
    # smoke test: spawns only on empty cells and assigns 2 or 4
    rng = random.Random(99)
    B = Board(rng)
    empties = sum(1 for r in B.grid for v in r if v == 0)
    assert 0 <= empties <= 14
    vals = {v for row in B.grid for v in row if v}
    assert vals.issubset({2,4})



if __name__ == "__main__":
    test_single_merge_per_move()
    test_no_spawn_on_illegal_move()
    test_game_over_detection()
    test_spawn_probability_shape_only()
    print("All deterministic tests passed.")

