"""Check the Gurobi MIP backend against independent Sudoku fixtures."""

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from test_puzzle_dataset import CASES, read_fixture, valid_solution


ROOT = Path(__file__).resolve().parents[1]
ENABLED = (
    importlib.util.find_spec("gurobipy") is not None
    and os.environ.get("SUDOKU_RUN_GUROBI") == "1"
)


@unittest.skipUnless(ENABLED, "install gurobipy and set SUDOKU_RUN_GUROBI=1")
class GurobiTests(unittest.TestCase):
    def check_cases(self, tier):
        from src.gurobi_solver import solve_sudoku_gurobi

        for case in (item for item in CASES if item["tier"] == tier):
            with self.subTest(case=case["id"]):
                puzzle = read_fixture(case["puzzle"])
                if case["expected"] == "INVALID":
                    with self.assertRaises(ValueError):
                        solve_sudoku_gurobi(puzzle)
                    continue
                result = solve_sudoku_gurobi(puzzle, num_workers=1)
                self.assertEqual(result.status, case["expected"])
                self.assertGreaterEqual(result.model_time, 0)
                self.assertGreaterEqual(result.solve_time, 0)
                if result.status == "SAT":
                    self.assertTrue(valid_solution(puzzle, result.solution))
                else:
                    self.assertIsNone(result.solution)

    def test_regular_cases(self):
        self.check_cases("regular")

    @unittest.skipUnless(os.environ.get("SUDOKU_RUN_LARGE") == "1",
                         "set SUDOKU_RUN_LARGE=1")
    def test_large_cases(self):
        self.check_cases("large")

    def test_invalid_settings(self):
        from src.gurobi_solver import solve_sudoku_gurobi

        for limit in (0, -1, float("inf"), float("nan"), True, "1"):
            with self.subTest(time_limit=limit), self.assertRaises(ValueError):
                solve_sudoku_gurobi([[0]], time_limit=limit)
        for workers in (0, -1, True, 1.5):
            with self.subTest(num_workers=workers), self.assertRaises(ValueError):
                solve_sudoku_gurobi([[0]], num_workers=workers)

    def test_cli_sat_unsat(self):
        def run(*args):
            return subprocess.run(
                [sys.executable, str(ROOT / "main.py"), "--solver", "gurobi", *args],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )

        sat = run("--stats", "data/test_puzzles/puzzles/04_blank_8.json")
        self.assertEqual(sat.returncode, 0, sat.stderr)
        self.assertIn("Solution:", sat.stdout)
        self.assertIn("Gurobi status:", sat.stdout)
        unsat = run("data/test_puzzles/puzzles/04_unsat_no_duplicate.json")
        self.assertEqual(unsat.returncode, 0, unsat.stderr)
        self.assertIn("Sudoku has no solution.", unsat.stdout)

    def test_cli_unknown_is_not_reported_as_unsat(self):
        import main
        from src.gurobi_solver import GurobiResult

        result = GurobiResult("UNKNOWN", "TIME_LIMIT", None, 0.0, 0.0)
        stderr = io.StringIO()
        with mock.patch.object(sys, "argv", ["main.py", "--solver", "gurobi"]), \
                mock.patch("src.gurobi_solver.solve_sudoku_gurobi", return_value=result), \
                contextlib.redirect_stderr(stderr), \
                self.assertRaises(SystemExit) as raised:
            main.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("TIME_LIMIT", stderr.getvalue())
        self.assertNotIn("no solution", stderr.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
