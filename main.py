"""Solve a Sudoku stored as a JSON array of rows; zero represents an empty cell."""

import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Solve an N x N Sudoku puzzle")
    parser.add_argument(
        "puzzle", nargs="?", type=Path,
        default=Path(__file__).resolve().parent / "data" / "puzzle.json",
        help="path to a JSON puzzle (default: data/puzzle.json)",
    )
    parser.add_argument("--solver", choices=("sat", "cp-sat", "gurobi"), default="sat",
                        help="solver to use (default: sat)")
    parser.add_argument("--time-limit", type=float, default=None,
                        help="CP-SAT or Gurobi solve time limit in seconds")
    parser.add_argument("--workers", type=int, default=None,
                        help="number of CP-SAT workers or Gurobi threads (default: 1)")
    parser.add_argument("--stats", action="store_true",
                        help="print model and solve times")
    args = parser.parse_args()

    if args.solver == "sat" and (args.time_limit is not None or args.workers is not None or args.stats):
        parser.error("--time-limit, --workers and --stats require --solver cp-sat or gurobi")

    try:
        with args.puzzle.open(encoding="utf-8") as puzzle_file:
            puzzle = json.load(puzzle_file)
        if args.solver == "sat":
            from src.solver import solve_sudoku
            solution = solve_sudoku(puzzle)
        elif args.solver == "cp-sat":
            from src.cp_sat_solver import solve_sudoku_cp_sat
            result = solve_sudoku_cp_sat(puzzle, time_limit=args.time_limit,
                                         num_workers=args.workers if args.workers is not None else 1)
            solution = result.solution
        else:
            from gurobipy import GurobiError
            from src.gurobi_solver import solve_sudoku_gurobi
            try:
                result = solve_sudoku_gurobi(
                    puzzle, time_limit=args.time_limit,
                    num_workers=args.workers if args.workers is not None else 1,
                )
            except GurobiError as error:
                parser.exit(2, f"Gurobi error: {error}\n")
            solution = result.solution
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    if args.solver == "cp-sat":
        if args.stats:
            from importlib.metadata import version
            print(f"OR-Tools version: {version('ortools')}")
            print(f"CP-SAT workers: {args.workers if args.workers is not None else 1}")
            print(f"CP-SAT time limit: {args.time_limit if args.time_limit is not None else 'none'}")
            print(f"CP-SAT status: {result.native_status}")
            print(f"Model build time: {result.model_time:.6f} s")
            print(f"Solve time: {result.solve_time:.6f} s")
        if result.status in ("UNKNOWN", "MODEL_INVALID"):
            parser.exit(2, f"CP-SAT could not determine a solution: {result.native_status}\n")
    elif args.solver == "gurobi":
        if args.stats:
            from importlib.metadata import version
            print(f"Gurobi version: {version('gurobipy')}")
            print(f"Gurobi threads: {args.workers if args.workers is not None else 1}")
            print(f"Gurobi time limit: {args.time_limit if args.time_limit is not None else 'none'}")
            print(f"Gurobi status: {result.native_status}")
            print(f"Model build time: {result.model_time:.6f} s")
            print(f"Solve time: {result.solve_time:.6f} s")
        if result.status == "UNKNOWN":
            parser.exit(2, f"Gurobi could not determine a solution: {result.native_status}\n")
    if solution is None:
        print("Sudoku has no solution.")
    else:
        print("Solution:")
        for row in solution:
            print(*row)


if __name__ == "__main__":
    main()
