# Generalized Sudoku solvers

This project solves generalized Sudoku with SAT, OR-Tools CP-SAT, or Gurobi MIP. A board has size `N x N`, where `N` is a positive perfect square (for example, 4, 9, 16, 25, or 100). Each block has size `sqrt(N) x sqrt(N)`.

Puzzles are JSON arrays of `N` rows, each containing `N` integers. Values from `1` to `N` are clues; `0` denotes an empty cell. See [data/puzzle.json](data/puzzle.json) for an example.

## Install and run

From the project root in PowerShell, create a virtual environment and install the dependencies:

```powershell
py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the default puzzle with the SAT solver, or provide another JSON file:

```powershell
& .\.venv\Scripts\python.exe main.py
& .\.venv\Scripts\python.exe main.py data/puzzle.json
```

Select CP-SAT or Gurobi with `--solver`:

```powershell
& .\.venv\Scripts\python.exe main.py --solver cp-sat data/puzzle.json
& .\.venv\Scripts\python.exe main.py --solver gurobi data/puzzle.json
```

The SAT solver is the default. It represents each cell-value choice with a Boolean variable and uses a sequential-counter encoding for exactly-one constraints. The generated clauses are passed to the solver incrementally, but large boards can still require substantial time and memory. A `100 x 100` puzzle is not guaranteed to complete on a given machine.

CP-SAT uses one integer variable per cell with domain `1..N` and an `AllDifferent` constraint for each row, column, and block. Gurobi uses one binary variable per cell-value choice and exactly-one equations for cells, rows, columns, and blocks.

For CP-SAT and Gurobi, `--time-limit` sets a solver-call time limit in seconds, `--workers` sets the CP-SAT worker count or Gurobi thread count, and `--stats` prints model construction and solve times. Both solvers default to one worker or thread. These options are unavailable for the SAT backend. For example:

```powershell
& .\.venv\Scripts\python.exe main.py --solver cp-sat --time-limit 60 --workers 1 --stats data/puzzle.json
& .\.venv\Scripts\python.exe main.py --solver gurobi --time-limit 60 --workers 1 --stats data/puzzle.json
```

The time limit covers the solver call, not model construction. The printed times are Python wall-clock measurements and exclude solution decoding. If CP-SAT returns `UNKNOWN` or `MODEL_INVALID`, the program reports that status without claiming the puzzle has no solution. Gurobi likewise reports an unknown outcome if its limit expires without a solution; if it has already found a solution, that solution is returned. An `OPTIMAL` status for this feasibility problem does not establish that a Sudoku solution is unique.

## Gurobi license

Gurobi requires a valid license. Place `gurobi.lic` in the project root, or set `GRB_LICENSE_FILE` to the full path of a license stored elsewhere. The program uses the project-root file automatically when the environment variable is unset.

## Tests and report

Run the standard test suite from the project root:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Gurobi tests require a license and are opt-in:

```powershell
$env:SUDOKU_RUN_GUROBI = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_GUROBI
```

See [the test dataset documentation](data/test_puzzles/README.md) for fixture provenance and optional larger tests. The [report directory](reports/sudoku_cp_sat_report/) contains the comparison of SAT, CP-SAT, and Gurobi MIP, including raw measurements and environment details.
