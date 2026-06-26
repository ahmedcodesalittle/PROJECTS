# Chess AI — Intelligent Browser Chess with Four AI Difficulty Levels

A full-stack browser-based chess game built with Python and Flask, featuring four progressively stronger AI opponents powered by classical game tree search algorithms. The project is designed as a portfolio demonstration of algorithms, web architecture, and UI engineering — not a tutorial clone.

---

## Live Demo Flow

```
Landing Page → Choose Difficulty → Choose Colour → Play → Post-Game Analysis → Play Again / Exit
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, python-chess |
| Frontend | HTML5, CSS3, Vanilla JavaScript (no frameworks) |
| Communication | Fetch API (JSON) between browser and Flask |
| Game State | Server-side session storage (FEN strings) |
| Fonts | Google Fonts — Rajdhani, Inter |

---

## Project Structure

```
chess_game/
├── app.py                  # Flask application, all routes
├── requirements.txt
├── bots/
│   ├── __init__.py
│   ├── beginner.py         # Random move selection
│   ├── intermediate.py     # Minimax / Negamax depth 3
│   ├── pro.py              # Alpha-Beta pruning depth 5
│   └── master.py           # Alpha-Beta + 3 optimisations depth 5
├── engine/
│   ├── __init__.py
│   └── evaluator.py        # Static position evaluator
├── static/
│   ├── css/style.css
│   └── js/game.js
└── templates/
    ├── index.html           # Level selection
    ├── choose.html          # Colour picker
    └── game.html            # Game board
```

---

## Algorithms

This is the technical core of the project. Each difficulty level uses a distinctly different algorithm from classical AI game theory.

---

### Level 1 — Beginner: Random Move Selection

**File:** `bots/beginner.py`

The simplest possible opponent. At each turn, all legal moves are collected from `board.legal_moves` and one is chosen using `random.choice()`. No evaluation is performed, no future positions are considered. The bot is equally likely to sacrifice its queen as to deliver checkmate.

**Why it matters:** Provides a meaningful baseline and makes the game accessible to complete beginners. It also demonstrates that even random play is valid chess — every move chosen is legal.

---

### Level 2 — Intermediate: Minimax (Negamax Formulation), Depth 3

**File:** `bots/intermediate.py`

**Algorithm:** Minimax is a foundational two-player zero-sum game tree search algorithm. It builds a tree of all reachable positions up to a fixed depth, evaluates the leaf nodes, and propagates scores back up the tree. The maximising player picks the move with the highest score; the minimising player picks the move with the lowest.

**Negamax simplification:** Rather than tracking two separate players (max and min), Negamax exploits the identity `min(a, b) = -max(-a, -b)`. Every recursive call simply maximises the negated score of its children — making the code uniform and easier to reason about.

**Depth 3** means the bot considers every sequence of 3 half-moves (plies): its move, your response, its next move. This is enough to avoid hanging pieces and see simple one-move tactics, but not enough to plan combinations.

**Pseudocode:**
```
function negamax(board, depth):
    if depth == 0 or game over:
        return evaluate(board)
    best = -infinity
    for each legal move:
        make move
        score = -negamax(board, depth - 1)
        undo move
        best = max(best, score)
    return best
```

**Complexity:** With an average branching factor of ~30, depth 3 examines approximately 27,000 nodes per move.

---

### Level 3 — Pro: Alpha-Beta Pruning, Depth 5

**File:** `bots/pro.py`

**Algorithm:** Alpha-Beta pruning is an optimisation of Minimax that eliminates branches of the game tree that cannot possibly affect the final decision. Two bounds are maintained throughout the search:

- **Alpha (α):** The best score the maximising side is guaranteed so far from any path already searched.
- **Beta (β):** The best score the minimising side is guaranteed so far from any path already searched.

When a node's score falls outside the `[α, β]` window, it is pruned — no further children need be examined. The reasoning: if the opponent already has a move that gives them at least β, and the current node gives the maximising side a score ≥ β, the opponent would never allow the game to reach this node, so there is no need to search it further.

**Why this is powerful:** In the best case (moves ordered perfectly), Alpha-Beta reduces the effective branching factor from `b^d` to `b^(d/2)`, effectively doubling the searchable depth for the same computational cost. At depth 5 with ~30 branching factor, this reduces from ~24 million to approximately 5,000 nodes in the best case.

**Pseudocode:**
```
function alpha_beta(board, depth, alpha, beta):
    if depth == 0 or game over:
        return evaluate(board)
    for each legal move:
        make move
        score = -alpha_beta(board, depth-1, -beta, -alpha)
        undo move
        if score >= beta:
            return beta          # Beta cutoff — opponent won't allow this
        alpha = max(alpha, score)
    return alpha
```

---

### Level 4 — Master: Alpha-Beta + Three Advanced Optimisations, Depth 5

**File:** `bots/master.py`

The Master bot applies three classical enhancements on top of Alpha-Beta that are used in real-world chess engines.

#### Enhancement 1 — Move Ordering (MVV-LVA)

**Most Valuable Victim, Least Valuable Attacker.** Alpha-Beta pruning is most effective when the best moves are searched first — this causes alpha to rise quickly, pruning more branches. MVV-LVA is a heuristic that sorts captures so that taking a high-value piece with a low-value piece is searched first.

```
ordering score = victim_value × 10 - attacker_value
```

A pawn capturing a queen scores highest `(9×10 - 1 = 89)`. A queen capturing a pawn scores low `(1×10 - 9 = 1)`. Additionally, the best move from the previous iteration of iterative deepening is always placed first.

#### Enhancement 2 — Transposition Table

Chess positions can be reached via many different sequences of moves (transpositions). Without a transposition table, the same position might be evaluated dozens of times during a single search. The transposition table is a Python dictionary keyed by the board's FEN string combined with the current search depth. Each entry stores the evaluated score and a flag indicating whether it is an exact score, a lower bound, or an upper bound.

```
key = board.fen() + str(depth)
table[key] = { "score": score, "flag": "exact" | "lower" | "upper" }
```

Before searching a node, the table is checked. If a sufficiently deep entry exists, it is returned immediately, avoiding redundant computation.

#### Enhancement 3 — Quiescence Search

The **horizon effect** is a known failure mode of fixed-depth search: the bot evaluates a position at depth 0 as static, missing a capture that occurs at depth 1. For example, the bot might think a rook is safe at depth 5, not realising it is immediately captured at depth 6.

Quiescence search addresses this by, at depth 0, not returning the static evaluation immediately. Instead, it continues searching **capture-only moves** until the position is "quiet" — no more captures are available. This ensures the bot never evaluates a position mid-exchange.

```
function quiesce(board, alpha, beta):
    stand_pat = evaluate(board)
    if stand_pat >= beta: return beta
    alpha = max(alpha, stand_pat)
    for each capture move:
        make move
        score = -quiesce(board, -beta, -alpha)
        undo move
        if score >= beta: return beta
        alpha = max(alpha, score)
    return alpha
```

#### Enhancement 4 — Iterative Deepening

Rather than searching directly to depth 5, the bot searches depth 1, then depth 2, up to depth 5 in sequence. The best move found at each shallower depth is used to seed move ordering for the next depth. This dramatically improves pruning efficiency because the likely best move is always searched first.

---

## Position Evaluator

**File:** `engine/evaluator.py`

The evaluation function converts a board position into a numerical score (in centipawns, where 100 = one pawn) from the perspective of the side to move. It has four components:

### Material Counting

| Piece | Value |
|---|---|
| Pawn | 100 |
| Knight | 320 |
| Bishop | 330 |
| Rook | 500 |
| Queen | 900 |
| King | 20,000 |

Bishop is valued slightly above Knight (330 vs 320) reflecting the known positional advantage of the bishop pair in open positions.

### Piece-Square Tables

Every piece type has a 64-value lookup table that adds a positional bonus or penalty based on where the piece stands on the board. For example:

- **Pawns** are rewarded for advancing toward the opponent's side and occupying the centre.
- **Knights** are penalised for being on the edge (`-50`) and rewarded for the centre (`+20`), reflecting their limited range from rim squares.
- **Bishops** are rewarded for open diagonals.
- **Kings** in the midgame are penalised for centralising (exposure to attack) and rewarded for castling.

Black pieces use `chess.square_mirror(sq)` to flip the table, so the same table works for both colours.

### Mobility Bonus

A bonus of `+10` is applied per legal move available to the side to move, rewarding active piece placement and penalising cramped positions.

### King Safety Penalty

A penalty is applied if the king has fewer than two pawns on the adjacent files in front of it, discouraging early pawn advances that leave the king exposed.

---

## How the Game Works

### Server-Side Architecture

The entire game state lives on the server as a FEN (Forsyth-Edwards Notation) string stored in Flask's session. FEN encodes the complete board position, castling rights, en passant target, and move counters in a single compact string. The frontend never needs to validate moves — all legality checking is handled server-side by python-chess.

### Route Map

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Level selection landing page |
| `/choose/<level>` | GET | Colour picker page |
| `/begin/<level>/<color>` | GET | Start game, bot moves first if player chose black |
| `/state` | GET | Return current board state as JSON |
| `/move` | POST | Accept player move, push bot response, return new state |
| `/restart` | POST | Reset board to starting position, return new state |

### Move Sequence

1. Player clicks a piece — legal destination squares are highlighted from `/state`'s `legal_moves` array.
2. Player clicks a destination — the move is applied to a local copy of the FEN immediately (instant visual feedback, no waiting for the server).
3. `POST /move` is sent with the UCI move string (e.g. `"e2e4"`).
4. Server validates legality, pushes the move, calls the bot, pushes the bot's response.
5. New state is returned; board re-renders with bot move highlighted in blue.

### Playing as Black

When the player chooses Black, the server calls `bot.get_move()` before rendering the game page, so the bot (White) has already made its first move when the board appears. The JavaScript board is flipped so the player's pieces always appear at the bottom, and file/rank labels update accordingly.

### Scoring

Captured piece values are computed by diffing material counts before and after each move using the same piece value table as the evaluator. Scores update live after every half-move.

### Post-Game Analysis

When the game ends, the modal analyses the game and surfaces insights:

- Whether the player was checkmated and their king was exposed
- Whether the bot gained a material advantage and by how much
- Whether the player relied too heavily on pawns in the opening

---

## What Makes This Different From Typical Chess Projects

Most chess projects on GitHub or tutorial sites fall into one of two categories: a pure frontend board with no AI at all, or a single-difficulty engine with no explanation of how it works. This project differs in several meaningful ways.

**Four genuinely distinct algorithms.** Each difficulty level uses a fundamentally different algorithm — not just a depth change. Beginner uses random selection, Intermediate uses Minimax, Pro adds Alpha-Beta pruning, and Master adds move ordering, transposition tables, and quiescence search. The progression mirrors the actual historical development of chess engine theory from the 1950s to the 1990s.

**Documented algorithm implementations.** Every bot file contains inline comments explaining what the algorithm is doing at each step and why. The evaluator labels each component clearly. The code is written to be read and learned from, not just executed.

**Full colour selection with board flip.** Playing as Black properly flips the board so your pieces are always at the bottom, file and rank labels update accordingly, and the bot automatically makes the first move. Most hobby chess projects only support playing as White.

**Live material scoring.** Captured piece values are tracked and displayed in real time for both sides, along with a material advantage badge that updates after every move.

**Separate move history tables.** Player moves and bot moves are displayed in separate scrollable panels side-by-side, making it easy to review the game at a glance.

**Post-game analysis.** The game-over modal surfaces specific observations about what went wrong — king exposure, material loss, opening mistakes — rather than simply declaring a winner.

**Instant visual feedback.** The player's move is rendered on the board immediately via local FEN manipulation in JavaScript before the server responds. The board does not freeze or flicker while the bot thinks.

**Clean server-side architecture.** All move validation happens server-side using python-chess, so the frontend cannot submit illegal moves. The game state is stored as a FEN string in the Flask session, making it trivially serialisable and stateless between requests.

**No external JavaScript libraries.** The entire frontend — board rendering, move highlighting, score tracking, modal system, board flip logic — is written in vanilla JavaScript. No jQuery, React, chess.js, or any other dependency.

**Only two Python dependencies.** Flask for the web server and python-chess for move validation. Nothing else.

---

## Difficulty Comparison

| | Beginner | Intermediate | Pro | Master |
|---|---|---|---|---|
| Algorithm | Random | Minimax | Alpha-Beta | Alpha-Beta + Optimisations |
| Search Depth | None | 3 ply | 5 ply | 5 ply + Quiescence |
| Move Ordering | None | None | None | MVV-LVA + iterative deepening hint |
| Position Cache | None | None | None | Transposition table |
| Horizon Effect | N/A | Present | Present | Resolved via quiescence search |
| Nodes per move (approx) | 1 | ~27,000 | ~5,000 pruned | Significantly fewer due to caching and ordering |

---

## Setup & Installation

```bash
# 1. Create the folder structure (Windows CMD)
mkdir chess_game
mkdir chess_game\bots
mkdir chess_game\engine
mkdir chess_game\static\css
mkdir chess_game\static\js
mkdir chess_game\templates

# 2. Create empty __init__.py files
type nul > chess_game\bots\__init__.py
type nul > chess_game\engine\__init__.py

# 3. Place all project files in their correct folders

# 4. Install dependencies
cd chess_game
pip install -r requirements.txt

# 5. Run
python app.py
```

Open `http://127.0.0.1:5000` in any browser.

---

## Dependencies

```
flask>=3.0.0
python-chess>=1.10.0
```

---

## Future Improvements

- Opening book integration (Lichess API) for stronger early game play
- Endgame tablebases for perfect play in simplified positions
- Time-limited search replacing fixed depth with a millisecond budget
- PGN export so games can be reviewed in external tools
- Multiplayer mode (two human players, same session)
- Stockfish integration as a fifth "Grandmaster" difficulty

---

## Author

Built by Abdul Hafeez Ahmed as a portfolio project demonstrating full-stack web development and classical AI algorithm implementation in Python.
