"use strict";

const PLAYER_COLOR = window.PLAYER_COLOR || "white";
const PIECE_POINTS = { p:1, n:3, b:3, r:5, q:9, k:0 };
const WHITE_GLYPHS = { K:"&#9812;", Q:"&#9813;", R:"&#9814;", B:"&#9815;", N:"&#9816;", P:"&#9817;" };
const BLACK_GLYPHS = { k:"&#9818;", q:"&#9819;", r:"&#9820;", b:"&#9821;", n:"&#9822;", p:"&#9823;" };

let state       = null;
let selected    = null;
let targets     = [];
let moveCount   = 0;
let playerScore = 0;
let botScore    = 0;
let playerMoves = [];
let botMoves    = [];

// If player is black, flip the board so black is at the bottom
const FLIPPED = (PLAYER_COLOR === "black");

function parseFen(fen) {
  const grid = [];
  for (const row of fen.split(" ")[0].split("/")) {
    const line = [];
    for (const ch of row) {
      if (/\d/.test(ch)) for (let i=0; i<+ch; i++) line.push(null);
      else line.push(ch);
    }
    grid.push(line);
  }
  return grid;
}

function sqName(r, c) {
  const col = FLIPPED ? 7-c : c;
  const row = FLIPPED ? r+1 : 8-r;
  return String.fromCharCode(97+col) + row;
}

function applyMoveLocally(fen, uci) {
  const grid = parseFen(fen);
  const fc=uci.charCodeAt(0)-97, fr=8-+uci[1];
  const tc=uci.charCodeAt(2)-97, tr=8-+uci[3];
  const promo=uci[4], piece=grid[fr][fc];
  grid[fr][fc]=null;
  grid[tr][tc]= promo&&piece ? (piece===piece.toUpperCase()?promo.toUpperCase():promo) : piece;
  const rows=grid.map(row=>{let s="",e=0;for(const sq of row){if(!sq)e++;else{if(e){s+=e;e=0;}s+=sq;}}if(e)s+=e;return s;});
  const parts=fen.split(" ");parts[0]=rows.join("/");return parts.join(" ");
}

function countMaterial(fen) {
  let w=0,b=0;
  for(const ch of fen.split(" ")[0]){
    if(/[A-Z]/.test(ch))w+=PIECE_POINTS[ch.toLowerCase()]||0;
    else if(/[a-z]/.test(ch))b+=PIECE_POINTS[ch]||0;
  }
  return {w,b};
}

function getCaptured(oldFen,newFen){
  const o=countMaterial(oldFen),n=countMaterial(newFen);
  return{whiteLost:o.w-n.w,blackLost:o.b-n.b};
}

function renderBoard(fen, opts={}) {
  const { hlFrom, hlTo, botFrom, botTo, lockAll } = opts;
  const board = document.getElementById("board");
  board.innerHTML = "";
  const grid = parseFen(fen);
  const turn = state ? state.turn : "white";

  for (let r=0; r<8; r++) {
    for (let c=0; c<8; c++) {
      const sq    = sqName(r, c);
      // Map display position back to grid
      const gc    = FLIPPED ? 7-c : c;
      const gr    = FLIPPED ? 7-r : r;
      const piece = grid[gr][gc];
      const cell  = document.createElement("div");
      cell.className = "sq " + ((gr+gc)%2===0 ? "light":"dark");
      cell.dataset.sq = sq;

      if (piece) {
        const span = document.createElement("span");
        const isW  = piece===piece.toUpperCase();
        span.className = "piece "+(isW?"piece-white":"piece-black");
        span.innerHTML = isW?(WHITE_GLYPHS[piece]||piece):(BLACK_GLYPHS[piece]||piece);
        cell.appendChild(span);

        // Make piece clickable only if it belongs to the player and it's their turn
        const isPlayerPiece = (PLAYER_COLOR==="white" && isW) || (PLAYER_COLOR==="black" && !isW);
        const isPlayerTurn  = turn===PLAYER_COLOR;
        if (!lockAll && isPlayerPiece && isPlayerTurn) cell.classList.add("clickable");
      }

      if (sq===hlFrom||sq===hlTo)  cell.classList.add("human-hi");
      if (sq===selected)            cell.classList.add("selected");
      if (targets.includes(sq))     cell.classList.add("can-move");
      if (sq===botFrom||sq===botTo) cell.classList.add("bot-hi");

      cell.addEventListener("click", ()=>onSquareClick(sq));
      board.appendChild(cell);
    }
  }

  // Update file/rank labels for flipped board
  const fl = document.getElementById("fileLabels");
  const rl = document.getElementById("rankLabels");
  if (fl) fl.innerHTML = (FLIPPED
    ? ["h","g","f","e","d","c","b","a"]
    : ["a","b","c","d","e","f","g","h"]
  ).map(x=>`<span>${x}</span>`).join("");
  if (rl) rl.innerHTML = (FLIPPED
    ? [1,2,3,4,5,6,7,8]
    : [8,7,6,5,4,3,2,1]
  ).map(x=>`<span>${x}</span>`).join("");
}

function onSquareClick(sq) {
  if (!state||state.status!=="playing") return;
  if (state.turn!==PLAYER_COLOR) return;
  if (selected&&targets.includes(sq)){ doMove(selected,sq); return; }
  const grid=parseFen(state.fen);
  const col=sq.charCodeAt(0)-97, row=8-+sq[1];
  const piece=grid[row][col];
  const isPlayerPiece=(PLAYER_COLOR==="white"&&piece===piece?.toUpperCase())||(PLAYER_COLOR==="black"&&piece&&piece!==piece.toUpperCase());
  if(!piece||!isPlayerPiece){selected=null;targets=[];renderBoard(state.fen);return;}
  selected=sq;
  targets=(state.legal_moves||[]).filter(m=>m.startsWith(sq)).map(m=>m.slice(2,4));
  renderBoard(state.fen);
}

async function doMove(from, to) {
  let uci=from+to;
  const grid=parseFen(state.fen);
  const piece=grid[8-+from[1]][from.charCodeAt(0)-97];
  // Promotion: white pawn to rank 8, black pawn to rank 1
  if(piece==="P"&&to[1]==="8") uci+="q";
  if(piece==="p"&&to[1]==="1") uci+="q";

  selected=null; targets=[];
  const preFen=state.fen;
  const localFen=applyMoveLocally(preFen, uci);
  renderBoard(localFen,{hlFrom:from,hlTo:to,lockAll:true});
  setThinking(true);
  await new Promise(r=>setTimeout(r,60));

  try {
    const res=await fetch("/move",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({move:uci})});
    const data=await res.json();
    setThinking(false);
    if(data.error){renderBoard(state.fen);return;}

    // Scoring
    const afterHuman=applyMoveLocally(preFen,uci);
    const hc=getCaptured(preFen,afterHuman);
    if(PLAYER_COLOR==="white"&&hc.blackLost>0) playerScore+=hc.blackLost;
    if(PLAYER_COLOR==="black"&&hc.whiteLost>0) playerScore+=hc.whiteLost;

    if(data.bot_move){
      const afterBot=applyMoveLocally(afterHuman,data.bot_move);
      const bc=getCaptured(afterHuman,afterBot);
      if(PLAYER_COLOR==="white"&&bc.whiteLost>0) botScore+=bc.whiteLost;
      if(PLAYER_COLOR==="black"&&bc.blackLost>0) botScore+=bc.blackLost;
    }

    moveCount++;
    playerMoves.push({num:moveCount,uci});
    if(data.bot_move) botMoves.push({num:moveCount,uci:data.bot_move});

    state=data;
    const bf=data.bot_move?data.bot_move.slice(0,2):null;
    const bt=data.bot_move?data.bot_move.slice(2,4):null;
    renderBoard(state.fen,{hlFrom:from,hlTo:to,botFrom:bf,botTo:bt});
    updatePanel();updateScores();updateMoveTables();
    if(data.status!=="playing") setTimeout(()=>showModal(data),900);
  } catch(e){setThinking(false);renderBoard(state.fen);}
}

function updatePanel(){
  if(!state)return;
  const g=id=>document.getElementById(id);
  if(g("iTurn"))   g("iTurn").textContent=state.turn==="white"?"White":"Black";
  if(g("iMove"))   g("iMove").textContent=moveCount+1;
  if(g("iStatus")) g("iStatus").textContent=state.status.charAt(0).toUpperCase()+state.status.slice(1);
}

function updateScores(){
  const g=id=>document.getElementById(id);
  if(g("playerScore")) g("playerScore").textContent=playerScore;
  if(g("botScore"))    g("botScore").textContent=botScore;
  const diff=playerScore-botScore;
  const adv=g("advantage");
  if(adv){
    adv.textContent=diff>0?"+"+diff+" You":diff<0?"+"+Math.abs(diff)+" Bot":"Even";
    adv.className="adv-badge "+(diff>0?"adv-player":diff<0?"adv-bot":"adv-even");
  }
}

function uciToLabel(uci){
  return uci.slice(0,2).toUpperCase()+"→"+uci.slice(2,4).toUpperCase()+(uci[4]?"=Q":"");
}

function updateMoveTables(){
  const pt=document.getElementById("playerMoves");
  const bt=document.getElementById("botMoves");
  if(pt){pt.innerHTML=playerMoves.map(m=>`<div class="move-row"><span class="move-num">${m.num}</span><span class="move-uci">${uciToLabel(m.uci)}</span></div>`).join("");pt.scrollTop=pt.scrollHeight;}
  if(bt){bt.innerHTML=botMoves.map(m=>`<div class="move-row"><span class="move-num">${m.num}</span><span class="move-uci">${uciToLabel(m.uci)}</span></div>`).join("");bt.scrollTop=bt.scrollHeight;}
}

function setThinking(on){
  const el=document.getElementById("thinking");
  if(el) el.hidden=!on;
}

function analyzeMistakes(finalStatus,finalTurn){
  const tips=[];
  if(finalStatus==="checkmate"){
    const playerLost=(PLAYER_COLOR==="white"&&finalTurn==="white")||(PLAYER_COLOR==="black"&&finalTurn==="black");
    if(playerLost) tips.push("Your king was checkmated. Look for when it became exposed and which pieces were missing to defend it.");
  }
  if(botScore>playerScore) tips.push(`The bot gained a ${botScore-playerScore} point material advantage. Try to avoid leaving pieces undefended.`);
  if(playerMoves.length>5){
    const earlyPawns=playerMoves.slice(0,6).filter(m=>m.uci[0]!=="n"&&m.uci[0]!=="b").length;
    if(earlyPawns>=4) tips.push("You moved many pawns in the opening. Develop your knights and bishops to active squares early.");
  }
  if(tips.length===0) tips.push("Well played! Review the game to find where you can improve further.");
  return tips;
}

function showModal(data){
  const modal=document.getElementById("modal");
  if(!modal)return;
  const playerLost=(PLAYER_COLOR==="white"&&data.turn==="white")||(PLAYER_COLOR==="black"&&data.turn==="black");
  document.getElementById("mIcon").innerHTML=playerLost?"&#9818;":"&#9812;";

  if(data.status==="checkmate"){
    document.getElementById("mTitle").textContent=playerLost?"You lost!":"You win!";
    document.getElementById("mMsg").textContent=(playerLost?"Bot wins":"You win")+" by checkmate. Score — You: "+playerScore+" pts | Bot: "+botScore+" pts";
  } else {
    document.getElementById("mTitle").textContent=data.status==="stalemate"?"Stalemate":"Draw";
    document.getElementById("mMsg").textContent="Game drawn. Score — You: "+playerScore+" pts | Bot: "+botScore+" pts";
  }

  const mb=document.getElementById("mMistakes");
  if(mb){
    const tips=analyzeMistakes(data.status,data.turn);
    mb.innerHTML="<strong>Game analysis:</strong><br>"+tips.map(t=>"• "+t).join("<br>");
    mb.hidden=false;
  }
  modal.hidden=false;
}

// Play Again — reset all state and fetch fresh board from server
document.addEventListener("DOMContentLoaded", ()=>{
  const btn=document.getElementById("playAgainBtn");
  if(btn) btn.addEventListener("click", async ()=>{
    try {
      const res=await fetch("/restart",{method:"POST"});
      const data=await res.json();
      // Reset all local state
      selected=null; targets=[]; moveCount=0;
      playerScore=0; botScore=0; playerMoves=[]; botMoves=[];
      state=data;
      document.getElementById("modal").hidden=true;
      renderBoard(state.fen);
      updatePanel(); updateScores(); updateMoveTables();
      // Clear mistake box
      const mb=document.getElementById("mMistakes");
      if(mb){mb.innerHTML="";mb.hidden=true;}
    } catch(e){console.error(e);}
  });

  init();
});

async function init(){
  try{
    const res=await fetch("/state");
    state=await res.json();
    renderBoard(state.fen);
    updatePanel();
    if(state.status!=="playing") showModal(state);
  } catch(e){console.error("Init failed:",e);}
}
