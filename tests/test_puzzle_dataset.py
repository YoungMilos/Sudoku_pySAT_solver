"""Validate the fixtures independently, then exercise the real SAT solver."""

import importlib.util
import itertools
import json
import math
import os
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data" / "test_puzzles"
MANIFEST = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
CASES = MANIFEST["cases"]


def read_fixture(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def valid_solution(puzzle, solution):
    """Check Sudoku rules and clues without calling the SAT encoder."""
    n = len(puzzle)
    box = math.isqrt(n)
    expected = set(range(1, n + 1))
    if len(solution) != n or any(len(row) != n for row in solution):
        return False
    if any(set(row) != expected for row in solution):
        return False
    if any({solution[r][c] for r in range(n)} != expected for c in range(n)):
        return False
    for br in range(0, n, box):
        for bc in range(0, n, box):
            if {solution[r][c] for r in range(br, br + box)
                for c in range(bc, bc + box)} != expected:
                return False
    return all(not puzzle[r][c] or puzzle[r][c] == solution[r][c]
               for r in range(n) for c in range(n))


class DatasetTests(unittest.TestCase):
    def test_references_and_independent_witnesses(self):
        ids = [case["id"] for case in CASES]
        self.assertEqual(len(ids), len(set(ids)))
        for case in CASES:
            with self.subTest(case=case["id"]):
                puzzle = read_fixture(case["puzzle"])
                self.assertEqual(len(puzzle), case["size"])
                if case["expected"] == "SAT":
                    self.assertTrue(valid_solution(puzzle, read_fixture(case["solution"])))

    def test_nontrivial_unsat_by_enumerating_4x4_solutions(self):
        case = next(case for case in CASES if case["id"] == "04_unsat_no_duplicate")
        puzzle = read_fixture(case["puzzle"])
        # This case is not solved merely by detecting duplicate clues.
        groups = puzzle + [[puzzle[r][c] for r in range(4)] for c in range(4)]
        groups += [[puzzle[r][c] for r in range(br, br + 2) for c in range(bc, bc + 2)]
                   for br in (0, 2) for bc in (0, 2)]
        for group in groups:
            clues = [value for value in group if value]
            self.assertEqual(len(clues), len(set(clues)))
        rows = list(itertools.permutations(range(1, 5)))
        empty = [[0] * 4 for _ in range(4)]
        solutions = [grid for grid in itertools.product(rows, repeat=4)
                     if valid_solution(empty, grid)]
        self.assertEqual(len(solutions), 288)
        self.assertFalse(any(valid_solution(puzzle, grid) for grid in solutions))

    def test_empty_4x4_has_multiple_solutions(self):
        case = next(case for case in CASES if case["id"] == "04_blank_16")
        puzzle = read_fixture(case["puzzle"])
        first = read_fixture(case["solution"])
        second = [[value % 4 + 1 for value in row] for row in first]
        self.assertNotEqual(first, second)
        self.assertTrue(valid_solution(puzzle, first))
        self.assertTrue(valid_solution(puzzle, second))


@unittest.skipUnless(importlib.util.find_spec("pysat"), "python-sat is not installed")
class DatasetSolverTests(unittest.TestCase):
    def run_cases(self, tier):
        from src.solver import solve_sudoku
        for case in (item for item in CASES if item["tier"] == tier):
            with self.subTest(case=case["id"]):
                puzzle = read_fixture(case["puzzle"])
                if case["expected"] == "INVALID":
                    with self.assertRaises(ValueError):
                        solve_sudoku(puzzle)
                else:
                    solution = solve_sudoku(puzzle)
                    if case["expected"] == "UNSAT":
                        self.assertIsNone(solution)
                    else:
                        self.assertIsNotNone(solution)
                        self.assertTrue(valid_solution(puzzle, solution))

    def test_regular_cases(self):
        self.run_cases("regular")

    @unittest.skipUnless(os.environ.get("SUDOKU_RUN_LARGE") == "1", "set SUDOKU_RUN_LARGE=1")
    def test_large_cases(self):
        self.run_cases("large")

    @unittest.skipUnless(os.environ.get("SUDOKU_RUN_STRESS") == "1", "set SUDOKU_RUN_STRESS=1")
    def test_100x100_stress(self):
        self.run_cases("stress")


if __name__ == "__main__":
    unittest.main()
