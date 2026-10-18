# Sudoku correctness test dataset

`manifest.json` lists each puzzle file, board size, expected result, and test tier. Files in `puzzles/` are JSON arrays that can be passed directly to `main.py`. For satisfiable cases, `solutions/` contains a corresponding example solution.

## Provenance and generation

All puzzles in this directory were generated for this project; none were copied from an external source. The `generate.py` script records the formula and random seeds needed to reproduce them:

- For `N = k²`, construct a completed grid with `grid[r][c] = (r*k + r//k + c + shift) % N + 1`.
- Remove the number of cells specified in the manifest using `random.Random(seed).sample` with a fixed seed. The original grid is saved as a witness that a solution exists. Removing cells does **not** establish uniqueness; the empty `4 x 4` puzzle has multiple solutions.
- The unsatisfiable cases were constructed for this dataset. Three have directly conflicting clues in a row, column, or block. `04_unsat_no_duplicate` has no immediate duplicate clue; an independent check enumerates all 288 completed `4 x 4` Sudoku grids and finds none compatible with its clues.
- The `invalid_*` files deliberately contain malformed shapes or out-of-range values and should raise `ValueError`. They are not unsatisfiable puzzles.

The example puzzle at `data/puzzle.json` predates this dataset. Its original source has not been verified, so no external attribution is claimed for it.

The satisfiable generated boards belong to one regular pattern family. This dataset is intended to check correctness; it is **not** a representative benchmark of puzzle difficulty or solver performance. In particular, the `100 x 100` example has only one empty cell.

## Run the tests

From the project root, after installing the dependencies in `.venv`:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The default suite covers cases up to `25 x 25` with SAT and CP-SAT when the corresponding packages are installed. Gurobi tests require a valid license and are enabled separately:

```powershell
$env:SUDOKU_RUN_GUROBI = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_GUROBI
```

Enable the `36 x 36` and `49 x 49` cases with `SUDOKU_RUN_LARGE`. This setting can be combined with `SUDOKU_RUN_GUROBI`:

```powershell
$env:SUDOKU_RUN_LARGE = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_LARGE
```

The optional `100 x 100` stress case can take significant time and memory. Run it only when the machine has sufficient resources:

```powershell
$env:SUDOKU_RUN_STRESS = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_STRESS
```

To regenerate the files managed by the script, run:

```powershell
& .\.venv\Scripts\python.exe data/test_puzzles/generate.py
```

This command overwrites fixtures with matching names and `manifest.json`.
