import chess
from engine.evaluator import evaluate

TT = {}

MVV = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9, chess.KING:100}

def order_moves(board, hint=None):
    def key(m):
        if hint and m == hint: return 10000
        if board.is_capture(m):
            v = board.piece_at(m.to_square)
            a = board.piece_at(m.from_square)
            if v and a:
                return MVV.get(v.piece_type,0)*10 - MVV.get(a.piece_type,0)
        return 0
    return sorted(board.legal_moves, key=key, reverse=True)

def quiesce(board, alpha, beta):
    stand = evaluate(board)
    if stand >= beta: return beta
    if stand > alpha: alpha = stand
    for move in board.legal_moves:
        if not board.is_capture(move): continue
        board.push(move)
        score = -quiesce(board, -beta, -alpha)
        board.pop()
        if score >= beta: return beta
        if score > alpha: alpha = score
    return alpha

def ab(board, depth, alpha, beta, hint=None):
    key = board.fen() + str(depth)
    if key in TT:
        e = TT[key]
        if e['flag'] == 'exact': return e['score']
        if e['flag'] == 'lower': alpha = max(alpha, e['score'])
        if e['flag'] == 'upper': beta  = min(beta,  e['score'])
        if alpha >= beta: return e['score']
    if depth == 0: return quiesce(board, alpha, beta)
    if board.is_game_over(): return evaluate(board)
    orig, best = alpha, -10**9
    for move in order_moves(board, hint):
        board.push(move)
        score = -ab(board, depth-1, -beta, -alpha)
        board.pop()
        if score > best: best = score
        if score > alpha: alpha = score
        if alpha >= beta: break
    TT[key] = {'score': best, 'flag': 'exact' if orig < best < beta else ('lower' if best >= beta else 'upper')}
    return best

def get_move(board):
    global TT
    TT = {}
    best = None
    for depth in range(1, 6):
        a, b = -10**9, 10**9
        current_best = None
        for move in order_moves(board, best):
            board.push(move)
            score = -ab(board, depth-1, -b, -a)
            board.pop()
            if score > a:
                a = score
                current_best = move
        if current_best:
            best = current_best
    return best
