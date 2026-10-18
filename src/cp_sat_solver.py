"""Solve square-block Sudoku puzzles with OR-Tools CP-SAT."""

from dataclasses import dataclass
from math import isfinite
from time import perf_counter

from ortools.sat.python import cp_model

from .encoder import validate_board


@dataclass(frozen=True)
class CpSatResult:
    """Solver outcome and wall-clock times, in seconds."""

    status: str
    native_status: str
    solution: list[list[int]] | None
    model_time: float
    solve_time: float


def solve_sudoku_cp_sat(board, *, time_limit=None, num_workers=1):
    """Return SAT, UNSAT, UNKNOWN, or MODEL_INVALID and an optional solution.

    The time limit applies to the CP-SAT solve call, not model construction.
    One worker is used by default to make comparisons with single-threaded
    solvers easier to reproduce.
    """
    size, box_size = validate_board(board)
    if time_limit is not None and (
        isinstance(time_limit, bool)
        or not isinstance(time_limit, (int, float))
        or not isfinite(time_limit)
        or time_limit <= 0
    ):
        raise ValueError("Time limit must be a finite positive number of seconds")
    if type(num_workers) is not int or num_workers < 1:
        raise ValueError("Number of workers must be a positive integer")

    start = perf_counter()
    model = cp_model.CpModel()
    cells = [[model.new_int_var(1, size, f"cell_{r}_{c}")
              for c in range(size)] for r in range(size)]

    for r in range(size):
        model.add_all_different(cells[r])
    for c in range(size):
        model.add_all_different([cells[r][c] for r in range(size)])
    for box_r in range(0, size, box_size):
        for box_c in range(0, size, box_size):
            model.add_all_different([
                cells[r][c]
                for r in range(box_r, box_r + box_size)
                for c in range(box_c, box_c + box_size)
            ])
    for r, row in enumerate(board):
        for c, value in enumerate(row):
            if value:
                model.add(cells[r][c] == value)
    model_time = perf_counter() - start

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = num_workers
    if time_limit is not None:
        solver.parameters.max_time_in_seconds = time_limit
    start = perf_counter()
    status = solver.solve(model)
    solve_time = perf_counter() - start

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution = [[solver.value(cells[r][c]) for c in range(size)]
                    for r in range(size)]
        outcome = "SAT"
    elif status == cp_model.INFEASIBLE:
        solution, outcome = None, "UNSAT"
    elif status == cp_model.MODEL_INVALID:
        solution, outcome = None, "MODEL_INVALID"
    else:
        solution, outcome = None, "UNKNOWN"

    return CpSatResult(outcome, solver.status_name(status), solution, model_time, solve_time)
