import importlib.util
import itertools
import json
import unittest
from pathlib import Path

from src.encoder import exactly_one, iter_sudoku_clauses, validate_board, var_id


def extend_by_unit_propagation(clauses, values):
    """Check a fully assigned Sudoku grid using unit propagation on auxiliaries."""
    values = dict(values)
    changed = True
    while changed:
        changed = False
        for clause in clauses:
            if any(values.get(abs(lit)) == (lit > 0) for lit in clause):
                continue
            unset = [lit for lit in clause if abs(lit) not in values]
            if not unset:
                return False
            if len(unset) == 1:
                lit = unset[0]
                values[abs(lit)] = lit > 0
                changed = True
    return True


def assignments_for_grid(grid):
    size = len(grid)
    return {var_id(r, c, v, size): grid[r][c] == v
            for r in range(size) for c in range(size)
            for v in range(1, size + 1)}


class EncodingTests(unittest.TestCase):
    def test_exactly_one_for_all_inputs(self):
        for n in range(1, 6):
            clauses = list(exactly_one(list(range(1, n + 1)), itertools.count(n + 1)))
            for bits in itertools.product((False, True), repeat=n):
                with self.subTest(n=n, bits=bits):
                    assignment = dict(enumerate(bits, start=1))
                    self.assertEqual(extend_by_unit_propagation(clauses, assignment),
                                     sum(bits) == 1)

    def test_sudoku_constraints_and_clues(self):
        grid = [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]]
        clues = [[1, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4]
        clauses = list(iter_sudoku_clauses(clues))
        self.assertTrue(extend_by_unit_propagation(clauses, assignments_for_grid(grid)))
        # Swap two cells: each cell still has one value, but row/column/box rules break.
        invalid = [row[:] for row in grid]
        invalid[0][1], invalid[1][1] = invalid[1][1], invalid[0][1]
        self.assertFalse(extend_by_unit_propagation(clauses, assignments_for_grid(invalid)))
        wrong_clue = [row[:] for row in grid]
        wrong_clue = [[(value % 4) + 1 for value in row] for row in wrong_clue]
        self.assertFalse(extend_by_unit_propagation(clauses, assignments_for_grid(wrong_clue)))

    def test_validation(self):
        for board in ([], [[0] * 3 for _ in range(3)], [[0] * 4 for _ in range(3)] + [[0]],
                      [[-1] * 4 for _ in range(4)], [[True] * 4 for _ in range(4)]):
            with self.subTest(board=board), self.assertRaises(ValueError):
                validate_board(board)
        self.assertEqual(validate_board([[0] * 100 for _ in range(100)]), (100, 10))

    def test_large_ids_and_incremental_generation(self):
        board = [[0] * 100 for _ in range(100)]
        self.assertEqual(var_id(99, 99, 100, 100), 1_000_000)
        clauses = list(itertools.islice(iter_sudoku_clauses(board), 3))
        self.assertEqual(clauses[0], list(range(1, 101)))
        self.assertEqual(clauses[1], [-1, 1_000_001])
        self.assertEqual(clauses[2], [-2, 1_000_002])


@unittest.skipUnless(importlib.util.find_spec("pysat"), "python-sat is not installed")
class SolverTests(unittest.TestCase):
    def test_solutions_and_unsat(self):
        from src.solver import solve_sudoku
        for size in (1, 4, 9, 16):
            box = int(size ** 0.5)
            expected = [[(r * box + r // box + c) % size + 1 for c in range(size)]
                        for r in range(size)]
            puzzle = [row[:] for row in expected]
            puzzle[0][0] = 0
            with self.subTest(size=size):
                self.assertEqual(solve_sudoku(puzzle), expected)
        contradiction = [[1, 1, 0, 0]] + [[0] * 4 for _ in range(3)]
        self.assertIsNone(solve_sudoku(contradiction))

    def test_default_puzzle(self):
        from src.solver import solve_sudoku
        path = Path(__file__).resolve().parents[1] / "data" / "puzzle.json"
        puzzle = json.loads(path.read_text(encoding="utf-8"))
        solved = solve_sudoku(puzzle)
        self.assertEqual(solved[0], [5, 3, 4, 6, 7, 8, 9, 1, 2])


if __name__ == "__main__":
    unittest.main()
