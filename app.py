from flask import Flask, request, jsonify
import json, os
from datetime import date

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def default_data():
    return {
        "name": "", "water_goal": 8, "master_streak": 0,
        "last_full_day": "", "last_date": str(date.today()),
        "sleep": [], "water": 0, "steps": None,
        "spend_today": 0.0, "spend_log": [],
        "habits": [
            {"id": 1, "name": "Morning workout", "done": False, "streak": 0},
            {"id": 2, "name": "Read 20 mins",    "done": False, "streak": 0},
            {"id": 3, "name": "No sugar",         "done": False, "streak": 0},
            {"id": 4, "name": "Meditate",         "done": False, "streak": 0},
        ],
        "goals": [
            {"id": 1, "name": "Save $10,000", "current": 3200, "target": 10000, "unit": "$"},
            {"id": 2, "name": "Run a 5K",     "current": 3,    "target": 5,     "unit": "km"},
            {"id": 3, "name": "Read 12 books","current": 4,    "target": 12,    "unit": "books"},
        ],
    }

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except: pass
    d = default_data(); save(d); return d

def save(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def day_reset(data):
    today = str(date.today())
    if data.get("last_date") == today: return data
    all_done = all(h["done"] for h in data["habits"])
    data["master_streak"] = (data.get("master_streak", 0) + 1) if all_done else 0
    if all_done: data["last_full_day"] = data.get("last_date", "")
    for h in data["habits"]:
        h["streak"] = (h.get("streak", 0) + 1) if h["done"] else 0
        h["done"] = False
    data.update({"water": 0, "steps": None, "spend_today": 0.0, "last_date": today})
    save(data); return data

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#ffffff">
<title>My Life Dashboard</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
<style>
:root{--bg:#f5f5f0;--surface:#ffffff;--border:#e5e5e0;--border2:#d0d0c8;--text:#1a1a18;--text2:#666660;--text3:#999990;--green:#1D9E75;--green-bg:#E1F5EE;--green-text:#0F6E56;--blue:#185FA5;--blue-bg:#E6F1FB;--blue-text:#0C447C;--amber:#BA7517;--amber-bg:#FAEEDA;--amber-text:#854F0B;--red:#A32D2D;--red-bg:#FCEBEB;--red-text:#791F1F;--radius:14px}
@media(prefers-color-scheme:dark){:root{--bg:#141412;--surface:#1e1e1c;--border:#2e2e2a;--border2:#3a3a36;--text:#f0f0ec;--text2:#aaaaaa;--text3:#666660;--green-bg:#0a2e20;--green-text:#5DCAA5;--blue-bg:#0a1e35;--blue-text:#85B7EB;--amber-bg:#2e1e00;--amber-text:#EF9F27;--red-bg:#2e0a0a;--red-text:#F09595}}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);max-width:480px;margin:0 auto;min-height:100dvh;display:flex;flex-direction:column;overscroll-behavior:none}
.topbar{padding:env(safe-area-inset-top,16px) 20px 12px;background:var(--surface);border-bottom:0.5px solid var(--border);flex-shrink:0}
.topbar-inner{display:flex;justify-content:space-between;align-items:center;margin-top:8px}
.greeting{font-size:20px;font-weight:600;color:var(--text)}.date-lbl{font-size:12px;color:var(--text3);margin-top:2px}
.streak-pill{display:flex;align-items:center;gap:5px;background:var(--amber-bg);border-radius:20px;padding:6px 12px}
.streak-num{font-size:16px;font-weight:700;color:var(--amber-text)}.streak-lbl{font-size:11px;color:var(--amber-text)}
.body{flex:1;overflow-y:auto;padding:16px;padding-bottom:90px}
.section-lbl{font-size:10px;font-weight:600;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;margin:0 4px 8px}
.card{background:var(--surface);border:0.5px solid var(--border);border-radius:var(--radius);padding:14px 16px;margin-bottom:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.qc{background:var(--surface);border:0.5px solid var(--border);border-radius:var(--radius);padding:13px}
.qc-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.qc-lbl{font-size:12px;color:var(--text2);display:flex;align-items:center;gap:4px}
.qc-val{font-size:26px;font-weight:600;color:var(--text);line-height:1}.qc-unit{font-size:11px;color:var(--text3);margin-top:2px}
.log-btn{background:var(--bg);border:0.5px solid var(--border2);border-radius:6px;padding:4px 8px;font-size:11px;color:var(--text2);cursor:pointer;display:flex;align-items:center;gap:3px;font-family:inherit}
.log-btn:active{opacity:.7;transform:scale(.95)}
.bar{height:5px;background:var(--bg);border-radius:3px;margin-top:8px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px;transition:width .4s ease}
.habit-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:0.5px solid var(--border)}.habit-row:last-child{border-bottom:none}
.hcheck{width:32px;height:32px;border-radius:50%;border:1.5px solid var(--border2);cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s;background:none}
.hcheck.done{background:var(--green);border-color:var(--green)}.hcheck.done i{color:#fff}
.hname{flex:1;font-size:14px;color:var(--text)}.hstreak{font-size:12px;color:var(--text3);display:flex;align-items:center;gap:3px}.hstreak.hot{color:#EF9F27}
.goal-row{padding:12px 0;border-bottom:0.5px solid var(--border)}.goal-row:last-child{border-bottom:none}
.goal-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.goal-name{font-size:14px;color:var(--text)}.goal-actions{display:flex;align-items:center;gap:6px}
.goal-pct{font-size:12px;font-weight:600;color:var(--text2)}.goal-sub{font-size:12px;color:var(--text3);margin-bottom:6px}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.stat-box{background:var(--bg);border-radius:10px;padding:12px}
.stat-val{font-size:22px;font-weight:600;color:var(--text)}.stat-lbl{font-size:11px;color:var(--text3);margin-top:2px}
.log-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:0.5px solid var(--border)}.log-row:last-child{border-bottom:none}
.log-desc{font-size:14px;color:var(--text)}.log-sub{font-size:11px;color:var(--text3);margin-top:1px}.log-amt{font-size:14px;font-weight:600;color:var(--text)}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:500}
.badge-green{background:var(--green-bg);color:var(--green-text)}.badge-amber{background:var(--amber-bg);color:var(--amber-text)}.badge-red{background:var(--red-bg);color:var(--red-text)}
.add-btn{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;padding:11px;border:0.5px dashed var(--border2);border-radius:10px;background:none;color:var(--text2);font-size:13px;cursor:pointer;margin-top:10px;font-family:inherit}
.add-btn:active{background:var(--bg)}
.nav{display:flex;background:var(--surface);border-top:0.5px solid var(--border);padding:8px 0;padding-bottom:max(env(safe-area-inset-bottom,0px),8px);position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:0 auto}
.nb{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;background:none;border:none;cursor:pointer;padding:4px 0;font-size:10px;color:var(--text3);font-family:inherit}
.nb.active{color:var(--green)}.nb i{font-size:22px}
.tab{display:none}.tab.active{display:block}
.empty{text-align:center;padding:24px 0;color:var(--text3);font-size:13px}
.settings-row{display:flex;justify-content:space-between;align-items:center;padding:13px 0;border-bottom:0.5px solid var(--border);cursor:pointer}.settings-row:last-child{border-bottom:none}.settings-row:active{opacity:.7}
.s-label{font-size:14px;color:var(--text)}.s-sub{font-size:12px;color:var(--text3);margin-top:1px}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:flex-end;justify-content:center}.overlay.open{display:flex}
.sheet{background:var(--surface);border-radius:20px 20px 0 0;padding:20px 20px max(env(safe-area-inset-bottom,16px),20px);width:100%;max-width:480px;border-top:0.5px solid var(--border);max-height:85dvh;overflow-y:auto}
.sheet-handle{width:36px;height:4px;background:var(--border2);border-radius:2px;margin:0 auto 16px}
.sheet-title{font-size:17px;font-weight:600;margin-bottom:16px;color:var(--text)}
.field{margin-bottom:14px}.field label{display:block;font-size:12px;color:var(--text2);margin-bottom:6px;font-weight:500}
.field input,.field select{width:100%;padding:11px 14px;border:0.5px solid var(--border2);border-radius:10px;font-size:15px;background:var(--surface);color:var(--text);font-family:inherit;appearance:none;-webkit-appearance:none}
.field input:focus,.field select:focus{outline:2px solid var(--green);border-color:var(--green)}
.primary-btn{width:100%;padding:14px;border-radius:12px;background:var(--green);border:none;color:#fff;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;margin-top:4px}
.primary-btn:active{opacity:.85;transform:scale(.98)}
.danger-btn{width:100%;background:none;border:none;color:var(--red);font-size:13px;cursor:pointer;padding:12px 0;font-family:inherit;text-align:center}
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#1a1a18;color:#fff;padding:10px 20px;border-radius:20px;font-size:13px;z-index:200;opacity:0;transition:opacity .3s;pointer-events:none;white-space:nowrap}.toast.show{opacity:1}
.streak-card{text-align:center;padding:24px}.streak-big{font-size:56px;font-weight:700;color:#EF9F27;line-height:1}
.streak-desc{font-size:13px;color:var(--text2);margin-top:8px;line-height:1.5}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-inner">
    <div><div class="greeting" id="greetTxt">Hello</div><div class="date-lbl" id="dateTxt"></div></div>
    <div class="streak-pill"><i class="ti ti-flame" style="font-size:16px;color:#EF9F27"></i><span class="streak-num" id="masterNum">0</span><span class="streak-lbl">day streak</span></div>
  </div>
</div>
<div class="body" id="bodyEl">
  <div id="tab-home" class="tab active">
    <div style="height:8px"></div>
    <div class="section-lbl">quick log</div>
    <div class="grid2">
      <div class="qc"><div class="qc-top"><span class="qc-lbl"><i class="ti ti-moon" style="font-size:13px"></i> Sleep</span><button class="log-btn" onclick="openSheet('sleep')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div><div class="qc-val" id="q-sleep">—</div><div class="qc-unit">hrs last night</div></div>
      <div class="qc"><div class="qc-top"><span class="qc-lbl"><i class="ti ti-droplet" style="font-size:13px"></i> Water</span><button class="log-btn" onclick="openSheet('water')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div><div class="qc-val" id="q-water">0</div><div class="qc-unit" id="q-water-lbl">of 8 glasses</div><div class="bar"><div class="bar-fill" id="water-bar" style="width:0%;background:var(--green)"></div></div></div>
      <div class="qc"><div class="qc-top"><span class="qc-lbl"><i class="ti ti-run" style="font-size:13px"></i> Steps</span><button class="log-btn" onclick="openSheet('steps')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div><div class="qc-val" id="q-steps">—</div><div class="qc-unit">steps today</div></div>
      <div class="qc"><div class="qc-top"><span class="qc-lbl"><i class="ti ti-coin" style="font-size:13px"></i> Spent</span><button class="log-btn" onclick="openSheet('spend')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div><div class="qc-val" id="q-spend">$0</div><div class="qc-unit">today</div></div>
    </div>
    <div class="section-lbl">today's habits</div>
    <div class="card" id="home-habits"></div>
    <div class="section-lbl">goals</div>
    <div class="card" id="home-goals"></div>
  </div>
  <div id="tab-health" class="tab">
    <div style="height:8px"></div>
    <div class="section-lbl">this week</div>
    <div class="stat-grid">
      <div class="stat-box"><div class="stat-val" id="h-sleep">—</div><div class="stat-lbl">avg sleep (hrs)</div></div>
      <div class="stat-box"><div class="stat-val" id="h-steps">—</div><div class="stat-lbl">steps today</div></div>
      <div class="stat-box"><div class="stat-val" id="h-water">—</div><div class="stat-lbl">water today</div></div>
      <div class="stat-box"><div class="stat-val" id="h-habits">0/0</div><div class="stat-lbl">habits done today</div></div>
    </div>
    <div class="section-lbl">sleep history</div>
    <div class="card" id="h-sleeplog"></div>
  </div>
  <div id="tab-money" class="tab">
    <div style="height:8px"></div>
    <div class="stat-grid">
      <div class="stat-box"><div class="stat-val" id="m-today">$0</div><div class="stat-lbl">spent today</div></div>
      <div class="stat-box"><div class="stat-val" id="m-week">$0</div><div class="stat-lbl">this week</div></div>
    </div>
    <div class="section-lbl">expense log</div>
    <div class="card"><div id="m-log"></div><button class="add-btn" onclick="openSheet('spend')"><i class="ti ti-plus" style="font-size:14px"></i> add expense</button></div>
  </div>
  <div id="tab-goals" class="tab">
    <div style="height:8px"></div>
    <div class="section-lbl">my goals</div>
    <div class="card" id="g-goals"></div>
    <button class="add-btn" onclick="openSheet('addGoal')"><i class="ti ti-plus" style="font-size:14px"></i> add goal</button>
    <div style="height:16px"></div>
    <div class="section-lbl">habits</div>
    <div class="card" id="g-habits"></div>
    <button class="add-btn" onclick="openSheet('addHabit')"><i class="ti ti-plus" style="font-size:14px"></i> add habit</button>
  </div>
  <div id="tab-you" class="tab">
    <div style="height:8px"></div>
    <div class="section-lbl">your streak</div>
    <div class="card streak-card">
      <div class="streak-big" id="s-streakBig">0</div>
      <div style="font-size:13px;color:var(--amber-text);margin-top:4px;font-weight:500">days in a row</div>
      <div class="streak-desc">Complete <strong>every habit</strong> each day to grow your streak.<br>Miss even one and it resets to zero.</div>
    </div>
    <div class="section-lbl" style="margin-top:16px">settings</div>
    <div class="card">
      <div class="settings-row" onclick="openSheet('rename')"><div><div class="s-label">Your name</div><div class="s-sub" id="s-name">Tap to set</div></div><i class="ti ti-chevron-right" style="font-size:16px;color:var(--text3)"></i></div>
      <div class="settings-row" onclick="openSheet('waterGoal')"><div><div class="s-label">Daily water goal</div><div class="s-sub" id="s-waterGoal">8 glasses</div></div><i class="ti ti-chevron-right" style="font-size:16px;color:var(--text3)"></i></div>
    </div>
    <div class="section-lbl" style="margin-top:16px">data</div>
    <div class="card">
      <div class="settings-row" onclick="doReset()"><div><div class="s-label" style="color:var(--red)">Reset all data</div><div class="s-sub">Cannot be undone</div></div><i class="ti ti-trash" style="font-size:16px;color:var(--red)"></i></div>
    </div>
  </div>
</div>
<nav class="nav">
  <button class="nb active" onclick="switchTab('home',this)"><i class="ti ti-home"></i><span>Home</span></button>
  <button class="nb" onclick="switchTab('health',this)"><i class="ti ti-heart"></i><span>Health</span></button>
  <button class="nb" onclick="switchTab('money',this)"><i class="ti ti-coin"></i><span>Money</span></button>
  <button class="nb" onclick="switchTab('goals',this)"><i class="ti ti-target"></i><span>Goals</span></button>
  <button class="nb" onclick="switchTab('you',this)"><i class="ti ti-user"></i><span>You</span></button>
</nav>
<div class="overlay" id="overlay" onclick="overlayClick(event)">
  <div class="sheet"><div class="sheet-handle"></div><div id="sheetContent"></div></div>
</div>
<div class="toast" id="toast"></div>
<script>
let S={},sheetType='',sheetId=null;
async function fetchData(){const r=await fetch('/api/data');S=await r.json();renderAll();}
async function persist(){await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(S)});}
function today(){return new Date().toISOString().slice(0,10);}
function renderAll(){
  const h=new Date().getHours(),name=S.name?', '+S.name:'';
  document.getElementById('greetTxt').textContent=(h<12?'Good morning':h<17?'Good afternoon':'Good evening')+name;
  document.getElementById('dateTxt').textContent=new Date().toLocaleDateString('en-AU',{weekday:'long',day:'numeric',month:'long'});
  document.getElementById('masterNum').textContent=S.master_streak||0;
  document.getElementById('s-streakBig').textContent=S.master_streak||0;
  document.getElementById('s-name').textContent=S.name||'Tap to set';
  document.getElementById('s-waterGoal').textContent=(S.water_goal||8)+' glasses';
  renderHome();renderHealth();renderMoney();renderGoalsPage();
}
function renderHome(){
  const sl=S.sleep||[];
  document.getElementById('q-sleep').textContent=sl.length?parseFloat(sl[sl.length-1]).toFixed(1):'—';
  document.getElementById('q-water').textContent=S.water||0;
  document.getElementById('q-water-lbl').textContent='of '+(S.water_goal||8)+' glasses';
  document.getElementById('water-bar').style.width=Math.min((S.water||0)/(S.water_goal||8)*100,100)+'%';
  document.getElementById('q-steps').textContent=S.steps!=null?Number(S.steps).toLocaleString():'—';
  document.getElementById('q-spend').textContent='$'+Math.round(S.spend_today||0);
  const habits=S.habits||[];
  document.getElementById('home-habits').innerHTML=habits.length?habits.map(h=>`<div class="habit-row"><button class="hcheck${h.done?' done':''}" onclick="toggleHabit(${h.id})">${h.done?'<i class="ti ti-check" style="font-size:14px"></i>':''}</button><span class="hname">${h.name}</span><span class="hstreak${h.streak>=3?' hot':''}"><i class="ti ti-flame" style="font-size:12px"></i> ${h.streak}d</span></div>`).join(''):'<div class="empty">No habits yet — add some in Goals tab</div>';
  const goals=S.goals||[];
  document.getElementById('home-goals').innerHTML=goals.length?goals.map(g=>{const pct=Math.min(Math.round(g.current/g.target*100),100),col=pct>=80?'var(--green)':pct>=40?'var(--blue)':'var(--amber)';return`<div class="goal-row"><div class="goal-top"><span class="goal-name">${g.name}</span><span class="goal-pct">${pct}%</span></div><div class="goal-sub">${g.current}/${g.target} ${g.unit}</div><div class="bar"><div class="bar-fill" style="width:${pct}%;background:${col}"></div></div></div>`;}).join(''):'<div class="empty">No goals yet</div>';
}
function renderHealth(){
  const sl=S.sleep||[],week=sl.slice(-7);
  document.getElementById('h-sleep').textContent=week.length?(week.reduce((a,b)=>a+parseFloat(b),0)/week.length).toFixed(1):'—';
  document.getElementById('h-steps').textContent=S.steps!=null?Number(S.steps).toLocaleString():'—';
  document.getElementById('h-water').textContent=(S.water||0)+' glasses';
  const done=(S.habits||[]).filter(h=>h.done).length;
  document.getElementById('h-habits').textContent=done+'/'+(S.habits||[]).length;
  const logEl=document.getElementById('h-sleeplog');
  if(!sl.length){logEl.innerHTML='<div class="empty">Log sleep from home to see history</div>';return;}
  logEl.innerHTML=sl.slice(-10).reverse().map((v,i)=>{const d=new Date();d.setDate(d.getDate()-i);const q=v>=7?'<span class="badge badge-green">Good</span>':v>=5?'<span class="badge badge-amber">Fair</span>':'<span class="badge badge-red">Poor</span>';return`<div class="log-row"><div class="log-desc">${d.toLocaleDateString('en-AU',{weekday:'short',day:'numeric',month:'short'})}</div>${q}<span class="log-amt">${parseFloat(v).toFixed(1)} hrs</span></div>`;}).join('');
}
function renderMoney(){
  document.getElementById('m-today').textContent='$'+Math.round(S.spend_today||0);
  const logs=S.spend_log||[],now=Date.now(),weekAmt=logs.filter(e=>(now-new Date(e.date).getTime())<7*86400000).reduce((a,e)=>a+e.amt,0);
  document.getElementById('m-week').textContent='$'+Math.round(weekAmt);
  const logEl=document.getElementById('m-log');
  logEl.innerHTML=logs.length?logs.slice(-20).reverse().map(e=>`<div class="log-row"><div><div class="log-desc">${e.desc}</div><div class="log-sub">${e.cat} · ${e.date}</div></div><span class="log-amt">$${parseFloat(e.amt).toFixed(2)}</span></div>`).join(''):'<div class="empty">No expenses yet</div>';
}
function renderGoalsPage(){
  const goals=S.goals||[];
  document.getElementById('g-goals').innerHTML=goals.length?goals.map(g=>{const pct=Math.min(Math.round(g.current/g.target*100),100),col=pct>=80?'var(--green)':pct>=40?'var(--blue)':'var(--amber)';return`<div class="goal-row"><div class="goal-top"><span class="goal-name">${g.name}</span><div class="goal-actions"><span class="goal-pct">${pct}%</span><button class="log-btn" onclick="openSheet('updateGoal',${g.id})"><i class="ti ti-pencil" style="font-size:11px"></i> update</button><button class="log-btn" onclick="deleteGoal(${g.id})" style="color:var(--red)"><i class="ti ti-trash" style="font-size:11px"></i></button></div></div><div class="goal-sub">${g.current}/${g.target} ${g.unit}</div><div class="bar"><div class="bar-fill" style="width:${pct}%;background:${col}"></div></div></div>`;}).join(''):'<div class="empty">No goals yet!</div>';
  const habits=S.habits||[];
  document.getElementById('g-habits').innerHTML=habits.length?habits.map(h=>`<div class="habit-row"><button class="hcheck${h.done?' done':''}" onclick="toggleHabit(${h.id})">${h.done?'<i class="ti ti-check" style="font-size:14px"></i>':''}</button><span class="hname">${h.name}</span><div style="display:flex;align-items:center;gap:8px"><span class="hstreak${h.streak>=3?' hot':''}"><i class="ti ti-flame" style="font-size:12px"></i> ${h.streak}d</span><button class="log-btn" onclick="deleteHabit(${h.id})" style="color:var(--red)"><i class="ti ti-trash" style="font-size:11px"></i></button></div></div>`).join(''):'<div class="empty">No habits yet</div>';
}
function toggleHabit(id){const h=S.habits.find(h=>h.id===id);if(h){h.done=!h.done;persist();renderAll();}}
function deleteGoal(id){S.goals=S.goals.filter(g=>g.id!==id);persist();renderAll();}
function deleteHabit(id){S.habits=S.habits.filter(h=>h.id!==id);persist();renderAll();}
function openSheet(type,id=null){
  sheetType=type;sheetId=id;
  const c=document.getElementById('sheetContent');
  if(type==='sleep'){const last=S.sleep&&S.sleep.length?S.sleep[S.sleep.length-1]:7;c.innerHTML=`<div class="sheet-title">Log sleep</div><div class="field"><label>Hours slept last night</label><input type="number" id="si" min="0" max="24" step="0.5" value="${last}"></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  else if(type==='water'){c.innerHTML=`<div class="sheet-title">Log water</div><div class="field"><label>Glasses today</label><input type="number" id="si" min="0" max="30" step="1" value="${S.water||0}"></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  else if(type==='steps'){c.innerHTML=`<div class="sheet-title">Log steps</div><div class="field"><label>Steps today</label><input type="number" id="si" min="0" step="100" value="${S.steps||0}"></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  else if(type==='spend'){c.innerHTML=`<div class="sheet-title">Add expense</div><div class="field"><label>Amount ($)</label><input type="number" id="sa" min="0" step="0.5" value="0"></div><div class="field"><label>Description</label><input type="text" id="sd" placeholder="Coffee, groceries..."></div><div class="field"><label>Category</label><select id="sc"><option>Food & drink</option><option>Transport</option><option>Shopping</option><option>Health</option><option>Entertainment</option><option>Other</option></select></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  else if(type==='addGoal'){c.innerHTML=`<div class="sheet-title">Add goal</div><div class="field"><label>Goal name</label><input type="text" id="gn" placeholder="Save $5,000, Run a marathon..."></div><div class="field"><label>Current progress</label><input type="number" id="gc" min="0" value="0"></div><div class="field"><label>Target</label><input type="number" id="gt" min="1" value="100"></div><div class="field"><label>Unit (e.g. $, km, books)</label><input type="text" id="gu" placeholder="books"></div><button class="primary-btn" onclick="doSave()">Add goal</button>`;}
  else if(type==='updateGoal'){const g=S.goals.find(g=>g.id===id);c.innerHTML=`<div class="sheet-title">Update: ${g.name}</div><div class="field"><label>Current progress</label><input type="number" id="gu2" min="0" value="${g.current}"></div><div class="field"><label>New target</label><input type="number" id="gt2" min="1" value="${g.target}"></div><button class="primary-btn" onclick="doSave()">Save</button><button class="danger-btn" onclick="deleteGoal(${id});closeSheet()">Delete this goal</button>`;}
  else if(type==='addHabit'){c.innerHTML=`<div class="sheet-title">Add habit</div><div class="field"><label>Habit name</label><input type="text" id="hn" placeholder="Morning run, No phone after 9pm..."></div><button class="primary-btn" onclick="doSave()">Add habit</button>`;}
  else if(type==='rename'){c.innerHTML=`<div class="sheet-title">Your name</div><div class="field"><label>What should I call you?</label><input type="text" id="rn" value="${S.name||''}" placeholder="Your name"></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  else if(type==='waterGoal'){c.innerHTML=`<div class="sheet-title">Daily water goal</div><div class="field"><label>Glasses per day</label><input type="number" id="wg" min="1" max="20" value="${S.water_goal||8}"></div><button class="primary-btn" onclick="doSave()">Save</button>`;}
  document.getElementById('overlay').classList.add('open');
  setTimeout(()=>{const f=document.querySelector('#sheetContent input,#sheetContent select');if(f)f.focus();},200);
}
function doSave(){
  const t=sheetType;
  if(t==='sleep'){const v=parseFloat(document.getElementById('si').value);if(!isNaN(v)&&v>0){if(!S.sleep)S.sleep=[];S.sleep.push(Math.round(v*10)/10);toast('Sleep logged!');}}
  else if(t==='water'){const v=parseInt(document.getElementById('si').value);if(!isNaN(v))S.water=Math.max(0,v);toast('Water updated!');}
  else if(t==='steps'){const v=parseInt(document.getElementById('si').value);if(!isNaN(v))S.steps=Math.max(0,v);toast('Steps logged!');}
  else if(t==='spend'){const a=parseFloat(document.getElementById('sa').value),d=document.getElementById('sd').value||'Expense',cat=document.getElementById('sc').value;if(!isNaN(a)&&a>0){S.spend_today=Math.round((S.spend_today+a)*100)/100;if(!S.spend_log)S.spend_log=[];S.spend_log.push({amt:a,desc:d,cat,date:today()});toast('Expense added!');}}
  else if(t==='addGoal'){const n=document.getElementById('gn').value.trim(),c=parseFloat(document.getElementById('gc').value)||0,tg=parseFloat(document.getElementById('gt').value)||100,u=document.getElementById('gu').value.trim()||'';if(n){if(!S.goals)S.goals=[];S.goals.push({id:Date.now(),name:n,current:c,target:tg,unit:u});toast('Goal added!');}}
  else if(t==='updateGoal'){const g=S.goals.find(g=>g.id===sheetId);if(g){g.current=parseFloat(document.getElementById('gu2').value)||0;g.target=parseFloat(document.getElementById('gt2').value)||g.target;toast('Goal updated!');}}
  else if(t==='addHabit'){const n=document.getElementById('hn').value.trim();if(n){if(!S.habits)S.habits=[];S.habits.push({id:Date.now(),name:n,done:false,streak:0});toast('Habit added!');}}
  else if(t==='rename'){S.name=document.getElementById('rn').value.trim();toast('Saved!');}
  else if(t==='waterGoal'){const v=parseInt(document.getElementById('wg').value);if(!isNaN(v)&&v>0)S.water_goal=v;toast('Goal updated!');}
  persist();renderAll();closeSheet();
}
function closeSheet(){document.getElementById('overlay').classList.remove('open');}
function overlayClick(e){if(e.target===document.getElementById('overlay'))closeSheet();}
async function doReset(){if(!confirm('Reset ALL data?'))return;const r=await fetch('/api/reset',{method:'POST'});S=await r.json();renderAll();toast('Reset!');}
function switchTab(name,btn){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.nb').forEach(b=>b.classList.remove('active'));document.getElementById('tab-'+name).classList.add('active');btn.classList.add('active');document.getElementById('bodyEl').scrollTop=0;}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000);}
fetchData();
</script>
</body>
</html>"""

@app.route("/")
def index():
    day_reset(load())
    return HTML

@app.route("/api/data")
def api_data():
    return jsonify(day_reset(load()))

@app.route("/api/save", methods=["POST"])
def api_save():
    save(request.json)
    return jsonify({"ok": True})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    d = default_data(); save(d); return jsonify(d)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n✅  Life Dashboard running!")
    print(f"📱  Open: http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)
