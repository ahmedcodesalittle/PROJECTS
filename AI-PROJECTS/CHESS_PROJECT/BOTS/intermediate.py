import chess
from engine.evaluator import evaluate

def negamax(board, depth):
    if depth == 0 or board.is_game_over():
        return evaluate(board)
    best = -10**9
    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1)
        board.pop()
        if score > best:
            best = score
    return best

def get_move(board):
    best_move, best_score = None, -10**9
    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, 2)
        board.pop()
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
