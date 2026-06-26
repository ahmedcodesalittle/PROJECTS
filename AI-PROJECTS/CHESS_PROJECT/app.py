import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from bots import beginner, intermediate, pro, master

app = Flask(__name__)
app.secret_key = "chess-ai-2024"

BOTS = { "beginner":beginner, "intermediate":intermediate, "pro":pro, "master":master }
ALGO = {
    "beginner":     "Random Move Selection",
    "intermediate": "Minimax (Negamax) — Depth 3",
    "pro":          "Alpha-Beta Pruning — Depth 5",
    "master":       "Alpha-Beta + Move Ordering + Transposition Table + Quiescence",
}

def get_status(board):
    if board.is_checkmate(): return "checkmate"
    if board.is_stalemate(): return "stalemate"
    if board.is_insufficient_material() or board.is_seventyfive_moves(): return "draw"
    return "playing"

def board_json(board, level, color, bot_move=None):
    d = {
        "fen":         board.fen(),
        "turn":        "white" if board.turn == chess.WHITE else "black",
        "status":      get_status(board),
        "legal_moves": [m.uci() for m in board.legal_moves],
        "level":       level,
        "algo":        ALGO.get(level, ""),
        "player_color": color,
    }
    if bot_move: d["bot_move"] = bot_move
    return d

@app.route("/")
def index():
    return render_template("index.html", algo=ALGO)

@app.route("/choose/<level>")
def choose(level):
    if level not in BOTS: level = "beginner"
    return render_template("choose.html", level=level, algo=ALGO[level])

@app.route("/begin/<level>/<color>")
def begin(level, color):
    if level not in BOTS: level = "beginner"
    if color not in ("white","black"): color = "white"
    board = chess.Board()
    session["fen"]   = board.fen()
    session["level"] = level
    session["color"] = color

    # If player chose black, bot (white) moves first immediately
    if color == "black":
        bot = BOTS[level]
        m   = bot.get_move(board)
        if m: board.push(m)
        session["fen"] = board.fen()

    return render_template("game.html", level=level, algo=ALGO[level], color=color)

@app.route("/restart", methods=["POST"])
def restart():
    level = session.get("level", "beginner")
    color = session.get("color", "white")
    board = chess.Board()
    session["fen"] = board.fen()

    if color == "black":
        bot = BOTS.get(level, beginner)
        m   = bot.get_move(board)
        if m: board.push(m)
        session["fen"] = board.fen()

    return jsonify(board_json(chess.Board(session["fen"]), level, color))

@app.route("/state")
def state():
    fen   = session.get("fen",   chess.Board().fen())
    level = session.get("level", "beginner")
    color = session.get("color", "white")
    return jsonify(board_json(chess.Board(fen), level, color))

@app.route("/move", methods=["POST"])
def move():
    fen   = session.get("fen")
    level = session.get("level", "beginner")
    color = session.get("color", "white")
    if not fen: return jsonify({"error":"no game"}), 400

    board = chess.Board(fen)
    uci   = request.get_json(force=True).get("move","")
    try:    m = chess.Move.from_uci(uci)
    except: return jsonify({"error":"bad move"}), 400
    if m not in board.legal_moves: return jsonify({"error":"illegal"}), 400

    board.push(m)
    if board.is_game_over():
        session["fen"] = board.fen()
        return jsonify(board_json(board, level, color))

    bot   = BOTS.get(level, beginner)
    bot_m = bot.get_move(board)
    if bot_m: board.push(bot_m)

    session["fen"] = board.fen()
    return jsonify(board_json(board, level, color, bot_m.uci() if bot_m else None))

@app.route("/game")
def game():
    level = session.get("level","beginner")
    color = session.get("color","white")
    return render_template("game.html", level=level, algo=ALGO[level], color=color)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
