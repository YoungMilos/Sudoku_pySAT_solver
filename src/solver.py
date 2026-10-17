from pysat.solvers import Glucose3

from .encoder import iter_sudoku_clauses, validate_board

def decode_model(model, size=9):
    board = [[0] * size for _ in range(size)]
    for literal in model:
        if 0 < literal <= size ** 3:
            position, value = divmod(literal - 1, size)
            r, c = divmod(position, size)
            board[r][c] = value + 1
    return board

def solve_sudoku(board):
    size, _ = validate_board(board)
    with Glucose3() as solver:
        for clause in iter_sudoku_clauses(board):
            solver.add_clause(clause)
        if not solver.solve():
            return None
        return decode_model(solver.get_model(), size)
