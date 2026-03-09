from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from models import init_db
from routes import router as api_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(title="StudyMate Lite", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)


@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {"status": "ok"}


LANDING_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>StudyMate Lite — AI Flashcards</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f1a;color:#e4e4ef;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;display:flex;flex-direction:column}
header{text-align:center;padding:3rem 1rem 1rem}
header h1{font-size:2.4rem;background:linear-gradient(135deg,#ff9800,#f06292);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
header p{margin-top:.5rem;color:#aaa;font-size:1.05rem}
main{flex:1;max-width:640px;width:100%;margin:1.5rem auto;padding:0 1rem}
.card{background:#1a1a2e;border:1px solid #2a2a44;border-radius:12px;padding:1.5rem;margin-bottom:1.2rem}
.card h2{font-size:1.15rem;margin-bottom:.8rem;color:#ff9800}
textarea{width:100%;min-height:120px;background:#12121f;color:#e4e4ef;border:1px solid #333;border-radius:8px;padding:.75rem;font-size:.95rem;resize:vertical}
textarea:focus{outline:none;border-color:#ff9800}
.row{display:flex;gap:.6rem;align-items:center;margin-top:.8rem}
.btn{background:linear-gradient(135deg,#ff9800,#f06292);color:#fff;border:none;border-radius:8px;padding:.65rem 1.4rem;font-size:.95rem;cursor:pointer;font-weight:600;transition:opacity .2s}
.btn:hover{opacity:.85}
.btn:disabled{opacity:.4;cursor:not-allowed}
select{background:#12121f;color:#e4e4ef;border:1px solid #333;border-radius:8px;padding:.5rem;font-size:.9rem}
#result{display:none}
.fc{background:#12121f;border:1px solid #2a2a44;border-radius:8px;padding:1rem;margin-bottom:.8rem;cursor:pointer;transition:border-color .2s}
.fc:hover{border-color:#ff9800}
.fc-q{font-weight:600;margin-bottom:.4rem}
.fc-a{color:#81c784;display:none}
.fc.open .fc-a{display:block}
.note{text-align:center;color:#888;font-size:.85rem;margin-top:.6rem}
footer{text-align:center;padding:1.5rem;color:#555;font-size:.8rem}
footer a{color:#ff9800;text-decoration:none}
</style>
</head>
<body>
<header>
  <h1>StudyMate Lite</h1>
  <p>Paste your notes, get AI-powered flashcards instantly.</p>
</header>
<main>
  <div class="card">
    <h2>Create Flashcards</h2>
    <textarea id="notes" placeholder="Paste lecture notes, textbook passages, or any study material here…"></textarea>
    <div class="row">
      <select id="maxCards">
        <option value="3">3 cards</option>
        <option value="5" selected>5 cards</option>
        <option value="10">10 cards</option>
      </select>
      <button class="btn" id="genBtn" onclick="generate()">Generate</button>
    </div>
  </div>
  <div id="result" class="card">
    <h2>Your Flashcards <span id="count"></span></h2>
    <p class="note">Click a card to reveal the answer</p>
    <div id="cards"></div>
  </div>
</main>
<footer>
  Powered by <a href="https://vibedeploy-7tgzk.ondigitalocean.app" target="_blank">vibeDeploy</a>
  &middot; DigitalOcean Serverless Inference
  &middot; <a href="/docs">API Docs</a>
</footer>
<script>
async function generate(){
  const btn=document.getElementById('genBtn');
  const notes=document.getElementById('notes').value.trim();
  if(!notes){alert('Please paste some notes first.');return}
  btn.disabled=true;btn.textContent='Generating…';
  try{
    const r=await fetch('/api/v1/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:notes,max_cards:parseInt(document.getElementById('maxCards').value)})});
    const d=await r.json();
    const box=document.getElementById('cards');box.innerHTML='';
    const res=document.getElementById('result');
    if(!d.cards||d.cards.length===0){
      box.innerHTML='<p class="note">No flashcards generated. Try pasting more detailed notes.</p>';
      res.style.display='block';return
    }
    document.getElementById('count').textContent='('+d.cards.length+')';
    d.cards.forEach(c=>{
      const el=document.createElement('div');el.className='fc';
      el.innerHTML='<div class="fc-q">Q: '+esc(c.question)+'</div><div class="fc-a">A: '+esc(c.answer)+'</div>';
      el.onclick=()=>el.classList.toggle('open');
      box.appendChild(el)
    });
    res.style.display='block';
    res.scrollIntoView({behavior:'smooth'})
  }catch(e){alert('Error: '+e.message)}
  finally{btn.disabled=false;btn.textContent='Generate'}
}
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=LANDING_HTML, status_code=200)
