import chess
from engine.evaluator import evaluate

def alpha_beta(board, depth, alpha, beta):
    if depth == 0 or board.is_game_over():
        return evaluate(board)
    for move in board.legal_moves:
        board.push(move)
        score = -alpha_beta(board, depth - 1, -beta, -alpha)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def get_move(board):
    best_move, alpha = None, -10**9
    for move in board.legal_moves:
        board.push(move)
        score = -alpha_beta(board, 4, -10**9, 10**9)
        board.pop()
        if score > alpha:
            alpha = score
            best_move = move
    return best_move
