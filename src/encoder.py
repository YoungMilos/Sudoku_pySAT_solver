from itertools import count
from math import isqrt


def validate_board(board):
    if not isinstance(board, list) or not board:
        raise ValueError("Board must be a non-empty list of rows")

    size = len(board)
    box_size = isqrt(size)
    if box_size * box_size != size:
        raise ValueError("Board size must be a perfect square")
    if any(not isinstance(row, list) or len(row) != size for row in board):
        raise ValueError("Board must have N rows, each with N values")
    if any(type(value) is not int or not 0 <= value <= size
           for row in board for value in row):
        raise ValueError(f"Board values must be integers from 0 to {size}")
    return size, box_size


def var_id(r, c, v, size=9):
    return size * size * r + size * c + v


def exactly_one(variables, next_aux):
    yield variables
    if len(variables) <= 1:
        return

    previous = next(next_aux)
    yield [-variables[0], previous]
    for variable in variables[1:-1]:
        current = next(next_aux)
        yield [-variable, current]
        yield [-previous, current]
        yield [-variable, -previous]
        previous = current
    yield [-variables[-1], -previous]


def iter_sudoku_clauses(board):
    size, box_size = validate_board(board)
    next_aux = count(size ** 3 + 1)

    # Each cell has one value.
    for r in range(size):
        for c in range(size):
            yield from exactly_one(
                [var_id(r, c, v, size) for v in range(1, size + 1)], next_aux
            )

    # Each value occurs once in each row and column.
    for r in range(size):
        for v in range(1, size + 1):
            yield from exactly_one(
                [var_id(r, c, v, size) for c in range(size)], next_aux
            )
    for c in range(size):
        for v in range(1, size + 1):
            yield from exactly_one(
                [var_id(r, c, v, size) for r in range(size)], next_aux
            )

    # Each value occurs once in each box.
    for box_r in range(0, size, box_size):
        for box_c in range(0, size, box_size):
            for v in range(1, size + 1):
                yield from exactly_one(
                    [var_id(r, c, v, size)
                     for r in range(box_r, box_r + box_size)
                     for c in range(box_c, box_c + box_size)],
                    next_aux,
                )

    for r, row in enumerate(board):
        for c, value in enumerate(row):
            if value:
                yield [var_id(r, c, value, size)]


def encode_sudoku(board):
    from pysat.formula import CNF
    return CNF(from_clauses=iter_sudoku_clauses(board))
