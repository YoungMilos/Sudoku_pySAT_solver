"""Reproduce the report's isolated-process SAT/CP-SAT/Gurobi experiments."""
import argparse
import csv
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'test_puzzles'
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def valid(puzzle, solution):
    n = len(puzzle)
    k = math.isqrt(n)
    target = set(range(1, n + 1))
    return (len(solution) == n and all(len(row) == n and set(row) == target for row in solution)
            and all({solution[r][c] for r in range(n)} == target for c in range(n))
            and all({solution[r][c] for r in range(br, br + k) for c in range(bc, bc + k)} == target
                    for br in range(0, n, k) for bc in range(0, n, k))
            and all(not puzzle[r][c] or puzzle[r][c] == solution[r][c]
                    for r in range(n) for c in range(n)))


def worker(case, method):
    puzzle = json.loads((DATA / case['puzzle']).read_text(encoding='utf-8'))
    if method == 'SAT':
        from pysat.solvers import Glucose3
        from src.encoder import iter_sudoku_clauses
        from src.solver import decode_model
        start = time.perf_counter()
        with Glucose3() as solver:
            for clause in iter_sudoku_clauses(puzzle):
                solver.add_clause(clause)
            model_time = time.perf_counter() - start
            start = time.perf_counter()
            solved = solver.solve()
            solve_time = time.perf_counter() - start
            solution = decode_model(solver.get_model(), len(puzzle)) if solved else None
        status = 'SAT' if solved else 'UNSAT'
        native_status = status
    elif method == 'CP-SAT':
        from src.cp_sat_solver import solve_sudoku_cp_sat
        result = solve_sudoku_cp_sat(puzzle, num_workers=1)
        model_time, solve_time = result.model_time, result.solve_time
        status, native_status, solution = result.status, result.native_status, result.solution
    elif method == 'Gurobi':
        from src.gurobi_solver import solve_sudoku_gurobi
        result = solve_sudoku_gurobi(puzzle, num_workers=1)
        model_time, solve_time = result.model_time, result.solve_time
        status, native_status, solution = result.status, result.native_status, result.solution
    else:
        raise ValueError(f'Unknown method: {method}')
    correct = (status == case['expected'] and (status != 'SAT' or valid(puzzle, solution)))
    print(json.dumps(dict(status=status, native_status=native_status, correct=correct,
                          model_seconds=model_time, solve_seconds=solve_time,
                          total_seconds=model_time + solve_time)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', nargs=2, metavar=('CASE', 'METHOD'))
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()
    cases = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))['cases']
    if args.worker:
        case = next(c for c in cases if c['id'] == args.worker[0])
        worker(case, args.worker[1])
        return
    import pysat
    import ortools
    import gurobipy
    selected = [c for c in cases if c['size'] >= 4 and c['expected'] in ('SAT', 'UNSAT')]
    metadata = dict(python=platform.python_version(), platform=platform.platform(),
                    processor=platform.processor(), pysat=pysat.__version__,
                    ortools=ortools.__version__, gurobi=gurobipy.gurobi.version(),
                    repetitions=args.repetitions,
                    external_timeout_seconds=args.timeout, cp_sat_workers=1,
                    gurobi_threads=1,
                    date_local=time.strftime('%Y-%m-%d %H:%M:%S %z'))
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                metadata['processor_name'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0]
        except OSError:
            pass
    (OUTPUT / 'environment.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    fields = ['case', 'size', 'blank_cells', 'expected', 'method', 'repetition', 'status',
              'native_status', 'correct', 'model_seconds', 'solve_seconds', 'total_seconds']
    with (OUTPUT / 'results.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for case in selected:
            puzzle = json.loads((DATA / case['puzzle']).read_text(encoding='utf-8'))
            blank = sum(v == 0 for row in puzzle for v in row)
            methods = ['CP-SAT'] if case['size'] == 100 else ['SAT', 'CP-SAT', 'Gurobi']
            for repeat in range(1, args.repetitions + 1):
                for method in methods[::1 if repeat % 2 else -1]:
                    record = dict(case=case['id'], size=case['size'], blank_cells=blank,
                                  expected=case['expected'], method=method, repetition=repeat)
                    try:
                        result = subprocess.run([sys.executable, __file__, '--worker', case['id'], method],
                                                capture_output=True, text=True, timeout=args.timeout, check=True)
                        record.update(json.loads(result.stdout.strip()))
                    except subprocess.TimeoutExpired:
                        record.update(status='TIMEOUT', correct=False)
                    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
                        record.update(status='ERROR', correct=False)
                        print(f'ERROR {case["id"]} {method}: {exc}', file=sys.stderr)
                    writer.writerow(record)
                    file.flush()
                    print(f'{case["id"]} {method} #{repeat}: {record.get("status")} '
                          f'{record.get("total_seconds", "-")}', flush=True)
    if any(row['status'] in ('ERROR', 'TIMEOUT') or row['correct'] != 'True'
           for row in csv.DictReader((OUTPUT / 'results.csv').open(encoding='utf-8'))):
        raise SystemExit('Review incomplete or incorrect runs in results.csv')


if __name__ == '__main__':
    main()
