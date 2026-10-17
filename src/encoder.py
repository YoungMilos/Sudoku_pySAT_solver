from itertools import combinations
from pysat.formula import CNF

def var_id(r, c, v):
    return 81*r + 9*c + v

def exactly_one(cnf, variables):
    cnf.append(variables)
    for a, b in combinations(variables, 2):
        cnf.append([-a, -b])

def encode_sudoku(board):
    if len(board) != 9 or any(len(row) != 9 for row in board):
        raise ValueError("Board must be 9x9")

    if any(
        type(v) is not int or not 0 <= v <= 9
        for row in board for v in row
        ):
        raise ValueError("Values must be integers from 0 to 9")

    cnf = CNF();

    # 1. Each cell contains exactly one value.
    for r in range(9):
        for c in range(9):
            variables = [
                var_id(r, c, v)
                for v in range(1, 10)
            ]
            exactly_one(cnf, variables)

    # 2. Each value occurs exactly once per row.
    for r in range(9):
        for v in range(1, 10):
            variables = [
                var_id(r, c, v)
                for c in range(9)
            ]
            exactly_one(cnf, variables)

    # 3. Each value occurs exactly once per column.
    for c in range(9):
        for v in range(1, 10):
            variables = [
                var_id(r, c, v)
                for r in range(9)
            ]
            exactly_one(cnf, variables)

    # 4. Each value occurs exactly once per 3x3 box.
    for box_r in range(0, 9, 3):
        for box_c in range(0, 9, 3):
            for v in range(1, 10):
                variables = [
                    var_id(r, c, v)
                    for r in range(box_r, box_r + 3)
                    for c in range(box_c, box_c + 3)
                ]
                exactly_one(cnf, variables)

    # 5. Given clues.
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v != 0:
                cnf.append([var_id(r, c, v)])

    return cnf
