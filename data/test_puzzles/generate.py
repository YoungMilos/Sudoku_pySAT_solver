"""Recreate the deterministic, synthetic Sudoku correctness fixtures."""

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def write_json(relative, value):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def full_grid(size, shift=0):
    box = int(size ** 0.5)
    return [[(r * box + r // box + c + shift) % size + 1
             for c in range(size)] for r in range(size)]


def remove_cells(grid, count, seed):
    size = len(grid)
    puzzle = [row[:] for row in grid]
    for cell in random.Random(seed).sample(range(size * size), count):
        puzzle[cell // size][cell % size] = 0
    return puzzle


def main():
    cases = []

    def add(case_id, board, expected, description, *, solution=None, tier="regular", source="synthetic"):
        puzzle_file = f"puzzles/{case_id}.json"
        write_json(puzzle_file, board)
        case = {"id": case_id, "size": len(board), "puzzle": puzzle_file,
                "expected": expected, "tier": tier, "description": description,
                "source": source}
        if solution is not None:
            solution_file = f"solutions/{case_id}.json"
            write_json(solution_file, solution)
            case["solution"] = solution_file
        cases.append(case)

    add("01_empty", [[0]], "SAT", "1x1: single empty cell", solution=[[1]])
    add("01_solved", [[1]], "SAT", "1x1: already solved", solution=[[1]])

    configurations = [
        # size, number of removed cells, seed, value shift, tier
        (4, 8, 401, 0, "regular"), (4, 12, 402, 1, "regular"),
        (4, 16, 403, 0, "regular"),
        (9, 40, 901, 0, "regular"), (9, 60, 902, 1, "regular"),
        (16, 128, 1601, 0, "regular"), (16, 192, 1602, 1, "regular"),
        (25, 200, 2501, 0, "regular"), (25, 400, 2502, 1, "regular"),
        (36, 360, 3601, 0, "large"),
        (49, 490, 4901, 0, "large"),
        (100, 1, 10001, 0, "stress"),
    ]
    for size, blanks, seed, shift, tier in configurations:
        solution = full_grid(size, shift)
        puzzle = remove_cells(solution, blanks, seed)
        add(f"{size:02d}_blank_{blanks}", puzzle, "SAT",
            f"{size}x{size}: {blanks} empty cells, seed={seed}, value shift={shift}",
            solution=solution, tier=tier)

    add("04_unsat_row", [[1, 1, 0, 0], [0] * 4, [0] * 4, [0] * 4], "UNSAT",
        "Two clues with value 1 in the same row")
    add("04_unsat_column", [[1, 0, 0, 0], [0] * 4, [1, 0, 0, 0], [0] * 4], "UNSAT",
        "Two clues with value 1 in the same column, in different boxes")
    add("04_unsat_box", [[1, 0, 0, 0], [0, 1, 0, 0], [0] * 4, [0] * 4], "UNSAT",
        "Two clues with value 1 in the same box, in different rows and columns")
    add("04_unsat_no_duplicate", [[0, 0, 3, 0], [0, 0, 1, 4],
                                  [2, 0, 0, 3], [0, 0, 4, 0]], "UNSAT",
        "No directly conflicting clues; ruled out by enumerating all 288 4x4 solutions")
    add("invalid_empty", [], "INVALID", "Empty board")
    add("invalid_non_square_size", [[0] * 3 for _ in range(3)], "INVALID", "N=3 is not a perfect square")
    add("invalid_ragged", [[0] * 4 for _ in range(3)] + [[0, 0]], "INVALID", "A row has fewer than N cells")
    add("invalid_out_of_range", [[5, 0, 0, 0]] + [[0] * 4 for _ in range(3)], "INVALID",
        "Value 5 is outside the range 0..4")
    add("invalid_boolean", [[True, 0, 0, 0]] + [[0] * 4 for _ in range(3)], "INVALID",
        "A Boolean is not a valid Sudoku value")

    write_json("manifest.json", {"schema_version": 1, "cases": cases})
    print(f"Created {len(cases)} cases in {ROOT}")


if __name__ == "__main__":
    main()
