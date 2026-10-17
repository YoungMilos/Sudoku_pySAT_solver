from pysat.solvers import Glucose3
from .encoder import encode_sudoku, var_id


def decode_model(model):
    positive = set(lit for lit in model if lit > 0)
    board = [[0] * 9 for _ in range(9)]

    for r in range(9):
        for c in range(9):
            for v in range(1, 10):
                if var_id(r, c, v) in positive:
                    board[r][c] = v
                    break

    return board


def solve_sudoku(board):
    cnf = encode_sudoku(board)

    with Glucose3(bootstrap_with=cnf.clauses) as solver:
        if not solver.solve():
            return None

        model = solver.get_model()
        return decode_model(model)
