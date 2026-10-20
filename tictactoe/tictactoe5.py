"""
Tic Tac Toe Player
"""

import math

X = "X"
O = "O"
EMPTY = None

board_size = 10
win_length = 5

def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY] * board_size for _ in range(board_size)]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    x_count = sum(row.count(X) for row in board)
    o_count = sum(row.count(O) for row in board)
    return X if x_count == o_count else O


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    possible_moves = set()
    for i in range(board_size):
        for j in range(board_size):
            if board[i][j] is EMPTY:
                possible_moves.add((i, j))
    return possible_moves


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    i, j = action
    new_board = [row[:] for row in board]
    new_board[i][j] = player(board)
    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for i in range(board_size):
            for j in range(board_size):
                if board[i][j] is EMPTY:
                    continue
                for di, dj in directions:
                    ok = True
                    for k in range(win_length):
                        r, c = i + k * di, j + k * dj
                        if not (0 <= r < board_size and 0 <= c < board_size):
                            ok = False
                            break
                        if board[r][c] != board[i][j]:
                            ok = False
                            break
                    if ok:
                        return board[i][j]

    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board) is not None:
        return True

    # board is full and still no winner
    for row in board:
        if EMPTY in row:
            return False
    return True


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    w = winner(board)
    if w == X:
        return 1
    elif w == O:
        return -1
    else:
        return 0


def evaluate(board):
    """
    Heuristic score of 'board' from X's perspective.
    Positive = good for X, negative = good for O.
    Only meaningful on non-terminal boards (terminal boards go through utility).
    """
    # A 5-in-a-row is terminal and never reaches here, but keep it for safety.
    weights = {1: 1, 2: 10, 3: 100, 4: 1_000, 5: 100_000}
    score = 0

    for i in range(board_size):
        for j in range(board_size):
            for di, dj in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r, end_c = i + 4 * di, j + 4 * dj
                if not (0 <= end_r < board_size and 0 <= end_c < board_size):
                    continue

                x_count = o_count = 0
                for k in range(win_length):
                    cell = board[i + k * di][j + k * dj]
                    if cell == X:
                        x_count += 1
                    elif cell == O:
                        o_count += 1

                # "Dead" window — both players have stones in it. Worthless.
                if x_count and o_count:
                    continue
                if x_count:
                    score += weights[x_count]
                elif o_count:
                    score -= weights[o_count]

    return score


# ---------------------------------------------------------------------------
# Search helpers — keep alpha-beta fast
# ---------------------------------------------------------------------------

def _candidate_moves(board):
    """
    Empty cells within NEIGHBORHOOD of an existing stone, plus center on
    a fully empty board. Cuts branching from 100 to ~20-40 in practice.
    """
    empty = actions(board)
    if len(empty) == board_size * board_size:
        return [(board_size // 2, board_size // 2)]

    NEIGHBORHOOD = 2
    candidates = set()
    for i in range(board_size):
        for j in range(board_size):
            if board[i][j] is EMPTY:
                continue
            for di in range(-NEIGHBORHOOD, NEIGHBORHOOD + 1):
                for dj in range(-NEIGHBORHOOD, NEIGHBORHOOD + 1):
                    r, c = i + di, j + dj
                    if 0 <= r < board_size and 0 <= c < board_size:
                        if board[r][c] is EMPTY:
                            candidates.add((r, c))

    return list(candidates) if candidates else list(empty)


def _would_win(board, i, j, p):
    """
    True if placing `p` at (i, j) creates a 5-in-a-row through (i, j).
    O(4 directions × 5 cells) — cheap.
    """
    for di, dj in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1
        r, c = i + di, j + dj
        while 0 <= r < board_size and 0 <= c < board_size and board[r][c] == p:
            count += 1
            r += di; c += dj
        r, c = i - di, j - dj
        while 0 <= r < board_size and 0 <= c < board_size and board[r][c] == p:
            count += 1
            r -= di; c -= dj
        if count >= win_length:
            return True
    return False


def _ordered_moves(board):
    """
    Winning moves first, opponent-winning-blockers second, everything else
    last. Alpha-beta prunes aggressively when good moves are tried early;
    this ordering is the main reason depth-3 is playable in Python.
    """
    p = player(board)
    opp = O if p == X else X
    wins, blocks, rest = [], [], []

    for m in _candidate_moves(board):
        i, j = m
        if _would_win(board, i, j, p):
            wins.append(m)
        elif _would_win(board, i, j, opp):
            blocks.append(m)
        else:
            rest.append(m)

    return wins + blocks + rest


    
# ---------------------------------------------------------------------------
# Minimax with alpha-beta pruning
# ---------------------------------------------------------------------------

def minimax(board, depth=3):
    """
    Returns the optimal action for the current player on the board,
    using depth-limited alpha-beta search.
    Increase `depth` for stronger (and slower) play.
    """
    if terminal(board):
        return None

    INF = float("inf")
    WIN_SCORE = 10_000_000     # outranks any heuristic leaf

    def alphabeta(b, d, alpha, beta):
        if terminal(b):
            u = utility(b)
            return WIN_SCORE if u == 1 else -WIN_SCORE if u == -1 else 0
        if d == 0:
            return evaluate(b)

        if player(b) == X:
            value = -INF
            for move in _ordered_moves(b):
                value = max(value, alphabeta(result(b, move), d - 1, alpha, beta))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = INF
            for move in _ordered_moves(b):
                value = min(value, alphabeta(result(b, move), d - 1, alpha, beta))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    best_move = None
    alpha, beta = -INF, INF

    if player(board) == X:
        best_score = -INF
        for move in _ordered_moves(board):
            score = alphabeta(result(board, move), depth - 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
    else:
        best_score = INF
        for move in _ordered_moves(board):
            score = alphabeta(result(board, move), depth - 1, alpha, beta)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)

    return best_move
