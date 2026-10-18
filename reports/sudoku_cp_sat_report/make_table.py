"""Create the paper's LaTeX table from the raw benchmark observations."""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
groups = defaultdict(list)
order = []
with (HERE / 'results.csv').open(encoding='utf-8', newline='') as file:
    for row in csv.DictReader(file):
        case = row['case']
        if case not in order:
            order.append(case)
        groups[(case, row['method'])].append(row)

lines = [
    r'\begin{table}[!htbp]',
    r'\caption{Median model plus solve time in seconds over three repetitions. '
    r'SAT denotes Glucose3; Gurobi uses a binary MIP; NR denotes not run.}',
    r'\label{tab:results}',
    r'\centering',
    r'\begin{tabular}{lrrlrrr}',
    r'\toprule',
    r'Instance & $N$ & Blanks & Status & SAT (s) & CP-SAT (s) & Gurobi (s) \\',
    r'\midrule',
]
for case in order:
    sample = groups.get((case, 'SAT'), groups[(case, 'CP-SAT')])[0]
    values = []
    for method in ('SAT', 'CP-SAT', 'Gurobi'):
        records = groups.get((case, method), [])
        if len(records) != 3 or any(r['status'] != sample['expected'] or r['correct'] != 'True'
                                    for r in records):
            values.append('NR' if not records else 'incomplete')
        else:
            values.append(f"{statistics.median(float(r['total_seconds']) for r in records):.4f}")
    label = case.replace('_', r'\_')
    lines.append(f"{label} & {sample['size']} & {sample['blank_cells']} & "
                 f"{sample['expected']} & {values[0]} & {values[1]} & {values[2]} \\\\")
lines.extend([r'\bottomrule', r'\end{tabular}', r'\end{table}'])
(HERE / 'results_table.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
