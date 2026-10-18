"""Solve square-block Sudoku as a binary mixed-integer program."""

from dataclasses import dataclass
from math import isfinite
from os import environ
from pathlib import Path
from time import perf_counter

import gurobipy as gp
from gurobipy import GRB

from .encoder import validate_board


@dataclass(frozen=True)
class GurobiResult:
    """Solver outcome and measured wall-clock times, in seconds."""

    status: str
    native_status: str
    solution: list[list[int]] | None
    model_time: float
    solve_time: float


_NATIVE_STATUS = {
    GRB.OPTIMAL: "OPTIMAL",
    GRB.INFEASIBLE: "INFEASIBLE",
    GRB.INF_OR_UNBD: "INF_OR_UNBD",
    GRB.TIME_LIMIT: "TIME_LIMIT",
    GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
    GRB.INTERRUPTED: "INTERRUPTED",
    GRB.NUMERIC: "NUMERIC",
    GRB.SUBOPTIMAL: "SUBOPTIMAL",
    GRB.MEM_LIMIT: "MEM_LIMIT",
}


def solve_sudoku_gurobi(board, *, time_limit=None, num_workers=1):
    """Return a Gurobi MIP outcome for a generalized Sudoku puzzle.

    The time limit applies to optimization, not model construction. When the
    limit is reached with an incumbent, the result is SAT with native status
    TIME_LIMIT; without an incumbent it is UNKNOWN.
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

    # Respect an explicitly configured license; otherwise use the project file.
    local_license = Path(__file__).resolve().parents[1] / "gurobi.lic"
    if not environ.get("GRB_LICENSE_FILE") and local_license.is_file():
        environ["GRB_LICENSE_FILE"] = str(local_license)

    start = perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model("Sudoku", env=env) as model:
            x = model.addVars(size, size, size, vtype=GRB.BINARY, name="x")

            for r in range(size):
                for c in range(size):
                    model.addConstr(gp.quicksum(x[r, c, v] for v in range(size)) == 1)

            for r in range(size):
                for v in range(size):
                    model.addConstr(gp.quicksum(x[r, c, v] for c in range(size)) == 1)
            for c in range(size):
                for v in range(size):
                    model.addConstr(gp.quicksum(x[r, c, v] for r in range(size)) == 1)

            for box_r in range(0, size, box_size):
                for box_c in range(0, size, box_size):
                    for v in range(size):
                        model.addConstr(gp.quicksum(
                            x[r, c, v]
                            for r in range(box_r, box_r + box_size)
                            for c in range(box_c, box_c + box_size)
                        ) == 1)

            for r, row in enumerate(board):
                for c, value in enumerate(row):
                    if value:
                        model.addConstr(x[r, c, value - 1] == 1)

            model.Params.Threads = num_workers
            model.Params.SolutionLimit = 1
            if time_limit is not None:
                model.Params.TimeLimit = time_limit
            model_time = perf_counter() - start

            start = perf_counter()
            model.optimize()
            solve_time = perf_counter() - start

            native = _NATIVE_STATUS.get(model.Status, f"STATUS_{model.Status}")
            if model.SolCount > 0:
                solution = [
                    [next(v + 1 for v in range(size) if x[r, c, v].X > 0.5)
                     for c in range(size)]
                    for r in range(size)
                ]
                outcome = "SAT"
            elif model.Status == GRB.INFEASIBLE:
                solution, outcome = None, "UNSAT"
            else:
                solution, outcome = None, "UNKNOWN"

    return GurobiResult(outcome, native, solution, model_time, solve_time)
