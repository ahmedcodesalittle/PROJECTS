import random
import chess

def get_move(board):
    return random.choice(list(board.legal_moves))
