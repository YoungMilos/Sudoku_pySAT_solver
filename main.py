"""Solve a Sudoku stored as a JSON array of rows; zero represents an empty cell."""

import argparse
import json
from pathlib import Path

from src.solver import solve_sudoku


def main():
    parser = argparse.ArgumentParser(description="Solve an N x N Sudoku puzzle")
    parser.add_argument(
        "puzzle", nargs="?", type=Path,
        default=Path(__file__).resolve().parent / "data" / "puzzle.json",
        help="path to a JSON puzzle (default: data/puzzle.json)",
    )
    args = parser.parse_args()

    try:
        with args.puzzle.open(encoding="utf-8") as puzzle_file:
            puzzle = json.load(puzzle_file)
        solution = solve_sudoku(puzzle)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    if solution is None:
        print("Sudoku has no solution.")
    else:
        print("Solution:")
        for row in solution:
            print(*row)


if __name__ == "__main__":
    main()
