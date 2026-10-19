# Generalized Sudoku report

The paper in main.tex uses the Elsevier cas-sc single-column template with
a simplified title block that omits article information, keywords, and the abstract.
It is accompanied by the official cas-sc.cls and cas-common.sty template
files, sourced from https://ctan.org/pkg/els-cas-templates.

The original observations are in results.csv; environment.json records the
experiment configuration. The SAT, CP-SAT and Gurobi MIP comparisons use
three fresh processes per puzzle and method. The 100_blank_1 instance was
run only with CP-SAT and contains just one empty cell. The local Gurobi
license is ignored by Git and is not part of the report data.

From the project root, install requirements.txt, then run:

    & .\.venv\Scripts\python.exe reports\sudoku_cp_sat_report\benchmark.py
    & .\.venv\Scripts\python.exe reports\sudoku_cp_sat_report\make_table.py

The first command overwrites results.csv and environment.json. The second
updates results_table.tex. Review and update the numerical discussion in
main.tex before recompiling, since that prose describes the original
measurements. The process timeout applies to startup and execution; reported
time excludes startup, decoding and correctness checking.

Author: Nguyen Tran Hoang Hieu; student ID 24021477; class 2627I_INT3011E_3.
Supervisor: To Van Khanh.
