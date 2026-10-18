"""Check the CP-SAT backend against independent Sudoku fixtures."""

import importlib.util
import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from test_puzzle_dataset import CASES, read_fixture, valid_solution


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("ortools"), "ortools is not installed")
class CpSatTests(unittest.TestCase):
    def check_cases(self, tier):
        from src.cp_sat_solver import solve_sudoku_cp_sat

        for case in (item for item in CASES if item["tier"] == tier):
            with self.subTest(case=case["id"]):
                puzzle = read_fixture(case["puzzle"])
                if case["expected"] == "INVALID":
                    with self.assertRaises(ValueError):
                        solve_sudoku_cp_sat(puzzle)
                    continue
                result = solve_sudoku_cp_sat(puzzle)
                self.assertEqual(result.status, case["expected"])
                self.assertGreaterEqual(result.model_time, 0)
                self.assertGreaterEqual(result.solve_time, 0)
                if result.status == "SAT":
                    self.assertTrue(valid_solution(puzzle, result.solution))
                else:
                    self.assertIsNone(result.solution)

    def test_regular_cases(self):
        self.check_cases("regular")

    @unittest.skipUnless(os.environ.get("SUDOKU_RUN_LARGE") == "1", "set SUDOKU_RUN_LARGE=1")
    def test_large_cases(self):
        self.check_cases("large")

    @unittest.skipUnless(os.environ.get("SUDOKU_RUN_STRESS") == "1", "set SUDOKU_RUN_STRESS=1")
    def test_100x100_stress(self):
        self.check_cases("stress")

    def test_invalid_solver_settings(self):
        from src.cp_sat_solver import solve_sudoku_cp_sat

        for limit in (0, -1, float("inf"), float("nan"), True, "1"):
            with self.subTest(time_limit=limit), self.assertRaises(ValueError):
                solve_sudoku_cp_sat([[0]], time_limit=limit)
        for workers in (0, -1, True, 1.5):
            with self.subTest(num_workers=workers), self.assertRaises(ValueError):
                solve_sudoku_cp_sat([[0]], num_workers=workers)

    def test_unknown_and_invalid_are_not_unsat(self):
        from ortools.sat.python import cp_model
        from src.cp_sat_solver import solve_sudoku_cp_sat

        for native in (cp_model.UNKNOWN, cp_model.MODEL_INVALID):
            with self.subTest(status=native), mock.patch("src.cp_sat_solver.cp_model.CpSolver") as cls:
                cls.return_value.solve.return_value = native
                cls.return_value.status_name.return_value = str(native)
                result = solve_sudoku_cp_sat([[0]], time_limit=1)
                self.assertEqual(result.status, "UNKNOWN" if native == cp_model.UNKNOWN else "MODEL_INVALID")
                self.assertIsNone(result.solution)
                self.assertEqual(cls.return_value.parameters.num_search_workers, 1)
                self.assertEqual(cls.return_value.parameters.max_time_in_seconds, 1)

    def test_cli_sat_unsat_and_invalid_settings(self):
        def run(*args):
            return subprocess.run([sys.executable, str(ROOT / "main.py"), *args],
                                  cwd=ROOT, capture_output=True, text=True, timeout=30)

        sat = run("--solver", "cp-sat", "--stats", "data/test_puzzles/puzzles/04_blank_8.json")
        self.assertEqual(sat.returncode, 0, sat.stderr)
        self.assertIn("Solution:", sat.stdout)
        self.assertIn("Model build time:", sat.stdout)
        unsat = run("--solver", "cp-sat", "data/test_puzzles/puzzles/04_unsat_no_duplicate.json")
        self.assertEqual(unsat.returncode, 0, unsat.stderr)
        self.assertIn("Sudoku has no solution.", unsat.stdout)
        invalid = run("--solver", "cp-sat", "--time-limit", "0")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("Time limit", invalid.stderr)
        wrong_backend = run("--solver", "sat", "--time-limit", "1")
        self.assertNotEqual(wrong_backend.returncode, 0)
        self.assertIn("require --solver cp-sat", wrong_backend.stderr)

    def test_cli_unknown_and_invalid_are_not_reported_as_unsat(self):
        import main
        from src.cp_sat_solver import CpSatResult

        for outcome in ("UNKNOWN", "MODEL_INVALID"):
            result = CpSatResult(outcome, outcome, None, 0.0, 0.0)
            stderr = io.StringIO()
            with self.subTest(outcome=outcome), \
                    mock.patch.object(sys, "argv", ["main.py", "--solver", "cp-sat"]), \
                    mock.patch("src.cp_sat_solver.solve_sudoku_cp_sat", return_value=result), \
                    contextlib.redirect_stderr(stderr), \
                    self.assertRaises(SystemExit) as raised:
                main.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertIn(outcome, stderr.getvalue())
            self.assertNotIn("no solution", stderr.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
