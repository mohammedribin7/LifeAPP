from flask import Flask, request, jsonify
import json, os, urllib.request, urllib.error
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo('Australia/Melbourne')

app = Flask(__name__)

SUPABASE_URL = "https://qoezyiesnuxedjaclvfn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFvZXp5aWVzbnV4ZWRqYWNsdmZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk2MDkxODQsImV4cCI6MjA5NTE4NTE4NH0.qQMCBG2WSW3LoyUCaKc3KGL4GUOkwbsawy-Epkmio30"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def db(method, endpoint, body=None, extra=None):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    data = json.dumps(body).encode() if body else None
    h = {**HEADERS, **(extra or {})}
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            text = r.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        print(f"DB {e.code}: {e.read().decode()}")
        return None

def today():
    return datetime.now(MELBOURNE).strftime('%Y-%m-%d')

def default_settings():
    return {
        "name": "",
        "water_goal": 8,
        "master_streak": 0,
        "last_full_day": "",
        "habits": [
            {"id": 1, "name": "Morning workout", "streak": 0},
            {"id": 2, "name": "Read 20 mins",    "streak": 0},
            {"id": 3, "name": "No sugar",         "streak": 0},
            {"id": 4, "name": "Meditate",         "streak": 0},
        ],
        "goals": [
            {"id": 1, "name": "Save $10,000", "current": 3200, "target": 10000, "unit": "$"},
            {"id": 2, "name": "Run a 5K",     "current": 3,    "target": 5,     "unit": "km"},
            {"id": 3, "name": "Read 12 books","current": 4,    "target": 12,    "unit": "books"},
        ],
    }

def default_day(settings):
    return {
        "date": today(),
        "sleep": None,
        "water": 0,
        "steps": None,
        "spend_today": 0.0,
        "spend_log": [],
        "habits_done": [],  # list of habit ids completed
    }

# ── Settings (name, goals, habits, streaks) ──────────────────
def load_settings():
    rows = db("GET", "settings?id=eq.main")
    if rows and len(rows) > 0 and rows[0].get("data"):
        d = rows[0]["data"]
        deflt = default_settings()
        for k, v in deflt.items():
            if k not in d:
                d[k] = v
        return d
    s = default_settings()
    save_settings(s)
    return s

def save_settings(s):
    db("POST", "settings", {"id": "main", "data": s},
       extra={"Prefer": "resolution=merge-duplicates"})

# ── Daily logs ────────────────────────────────────────────────
def load_day(day_str):
    rows = db("GET", f"dailylogs?date=eq.{day_str}")
    if rows and len(rows) > 0:
        return rows[0]["data"]
    return None

def save_day(day_str, data):
    db("POST", "dailylogs", {"date": day_str, "data": data},
       extra={"Prefer": "resolution=merge-duplicates"})

def load_history(limit=30):
    rows = db("GET", f"dailylogs?order=date.desc&limit={limit}")
    if not rows:
        return []
    return [{"date": r["date"], **r["data"]} for r in rows]

def get_today_data(settings):
    t = today()
    day = load_day(t)
    if day is None:
        # New day — check if yesterday was completed for streak
        yesterday = str(date.today() - timedelta(days=1))
        yday = load_day(yesterday)
        if yday:
            habit_ids = [h["id"] for h in settings["habits"]]
            all_done = all(hid in yday.get("habits_done", []) for hid in habit_ids)
            if all_done:
                settings["master_streak"] = settings.get("master_streak", 0) + 1
                settings["last_full_day"] = yesterday
                # update individual streaks
                for h in settings["habits"]:
                    if h["id"] in yday.get("habits_done", []):
                        h["streak"] = h.get("streak", 0) + 1
                    else:
                        h["streak"] = 0
            else:
                settings["master_streak"] = 0
                for h in settings["habits"]:
                    if h["id"] not in yday.get("habits_done", []):
                        h["streak"] = 0
            save_settings(settings)
        day = default_day(settings)
        save_day(t, day)
    return day

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#ffffff">
<title>My Life</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
<style>
:root{--bg:#f5f5f0;--surface:#fff;--border:#e5e5e0;--border2:#d0d0c8;--text:#1a1a18;--text2:#666660;--text3:#999990;--green:#1D9E75;--green-bg:#E1F5EE;--green-text:#0F6E56;--bgreen:#00C851;--bgreen-bg:#E0FFF0;--blue:#185FA5;--amber:#BA7517;--amber-bg:#FAEEDA;--amber-text:#854F0B;--orange:#D4620A;--orange-bg:#FDE8D8;--orange-text:#A04000;--red:#A32D2D;--red-bg:#FCEBEB;--red-text:#791F1F;--r:14px}
@media(prefers-color-scheme:dark){:root{--bg:#141412;--surface:#1e1e1c;--border:#2e2e2a;--border2:#3a3a36;--text:#f0f0ec;--text2:#aaaaaa;--text3:#666660;--green-bg:#0a2e20;--green-text:#5DCAA5;--bgreen-bg:#003318;--amber-bg:#2e1e00;--amber-text:#EF9F27;--orange-bg:#2e1200;--orange-text:#F08040;--red-bg:#2e0a0a;--red-text:#F09595}}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);max-width:480px;margin:0 auto;min-height:100dvh;display:flex;flex-direction:column}
.topbar{padding:env(safe-area-inset-top,16px) 20px 12px;background:var(--surface);border-bottom:0.5px solid var(--border);flex-shrink:0}
.topbar-inner{display:flex;justify-content:space-between;align-items:center;margin-top:6px}
.greeting{font-size:19px;font-weight:600}.date-lbl{font-size:12px;color:var(--text3);margin-top:2px}
.streak-pill{display:flex;align-items:center;gap:5px;background:var(--amber-bg);border-radius:20px;padding:5px 12px;flex-shrink:0}
.streak-num{font-size:15px;font-weight:700;color:var(--amber-text)}.streak-lbl{font-size:11px;color:var(--amber-text)}
.body{flex:1;overflow-y:auto;padding:16px;padding-bottom:90px}
.slbl{font-size:10px;font-weight:600;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;margin:0 4px 8px}
.card{background:var(--surface);border:0.5px solid var(--border);border-radius:var(--r);padding:14px 16px;margin-bottom:12px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.qc{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);padding:12px;transition:background .3s,border-color .3s}
.qc-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px}
.qc-lbl{font-size:12px;color:var(--text2);display:flex;align-items:center;gap:4px}
.qc-val{font-size:25px;font-weight:700;color:var(--text);line-height:1}
.qc-unit{font-size:11px;color:var(--text3);margin-top:2px}
.qc.sg{background:var(--green-bg);border-color:var(--green)}.qc.sg .qc-val,.qc.sg .qc-unit{color:var(--green-text)}
.qc.sbg{background:var(--bgreen-bg);border-color:var(--bgreen)}.qc.sbg .qc-val,.qc.sbg .qc-unit{color:#007a30}
.qc.so{background:var(--orange-bg);border-color:var(--orange)}.qc.so .qc-val,.qc.so .qc-unit{color:var(--orange-text)}
.crow{display:flex;align-items:center;gap:8px;margin-top:6px}
.cbtn{width:30px;height:30px;border-radius:50%;border:1.5px solid var(--border2);background:var(--bg);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px;color:var(--text2);flex-shrink:0;transition:all .15s}
.cbtn:active{transform:scale(.85)}
.cval{flex:1;text-align:center;font-size:25px;font-weight:700;color:var(--text)}
.cunit{font-size:11px;color:var(--text3);text-align:center;margin-top:1px}
.bar{height:5px;background:var(--bg);border-radius:3px;margin-top:8px;overflow:hidden}
.bf{height:100%;border-radius:3px;transition:width .4s,background .3s}
.lbtn{background:var(--bg);border:0.5px solid var(--border2);border-radius:6px;padding:4px 8px;font-size:11px;color:var(--text2);cursor:pointer;display:flex;align-items:center;gap:3px;font-family:inherit}
.lbtn:active{opacity:.7;transform:scale(.95)}
.hrow{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:0.5px solid var(--border)}.hrow:last-child{border-bottom:none}
.hchk{width:30px;height:30px;border-radius:50%;border:1.5px solid var(--border2);cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s;background:none}
.hchk.done{background:var(--green);border-color:var(--green)}
.hname{flex:1;font-size:14px}.hstr{font-size:12px;color:var(--text3);display:flex;align-items:center;gap:3px}.hstr.hot{color:#EF9F27}
.grow{padding:11px 0;border-bottom:0.5px solid var(--border)}.grow:last-child{border-bottom:none}
.gtop{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.gname{font-size:14px}.gact{display:flex;align-items:center;gap:6px}
.gpct{font-size:12px;font-weight:600;color:var(--text2)}.gsub{font-size:12px;color:var(--text3);margin-bottom:5px}
.sgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.sbox{background:var(--bg);border-radius:10px;padding:12px}
.sval{font-size:21px;font-weight:600}.slb{font-size:11px;color:var(--text3);margin-top:2px}
.lrow{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:0.5px solid var(--border)}.lrow:last-child{border-bottom:none}
.ldesc{font-size:14px}.lsub{font-size:11px;color:var(--text3);margin-top:1px}.lamt{font-size:14px;font-weight:600}
.bdg{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:500}
.bg{background:var(--green-bg);color:var(--green-text)}.ba{background:var(--amber-bg);color:var(--amber-text)}.br{background:var(--red-bg);color:var(--red-text)}
.addbtn{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;padding:10px;border:0.5px dashed var(--border2);border-radius:10px;background:none;color:var(--text2);font-size:13px;cursor:pointer;margin-top:8px;font-family:inherit}
.addbtn:active{background:var(--bg)}
.nav{display:flex;background:var(--surface);border-top:0.5px solid var(--border);padding:8px 0;padding-bottom:max(env(safe-area-inset-bottom,0px),8px);position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:0 auto}
.nb{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;background:none;border:none;cursor:pointer;padding:4px 0;font-size:10px;color:var(--text3);font-family:inherit}
.nb.active{color:var(--green)}.nb i{font-size:22px}
.tab{display:none}.tab.active{display:block}
.empty{text-align:center;padding:24px 0;color:var(--text3);font-size:13px}
.srow{display:flex;justify-content:space-between;align-items:center;padding:13px 0;border-bottom:0.5px solid var(--border);cursor:pointer}.srow:last-child{border-bottom:none}.srow:active{opacity:.7}
.sl{font-size:14px}.ss{font-size:12px;color:var(--text3);margin-top:1px}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:flex-end;justify-content:center}.overlay.open{display:flex}
.sheet{background:var(--surface);border-radius:20px 20px 0 0;padding:20px 20px max(env(safe-area-inset-bottom,16px),20px);width:100%;max-width:480px;max-height:85dvh;overflow-y:auto}
.shandle{width:36px;height:4px;background:var(--border2);border-radius:2px;margin:0 auto 16px}
.stitle{font-size:17px;font-weight:600;margin-bottom:16px}
.field{margin-bottom:14px}.field label{display:block;font-size:12px;color:var(--text2);margin-bottom:6px;font-weight:500}
.field input,.field select{width:100%;padding:11px 14px;border:0.5px solid var(--border2);border-radius:10px;font-size:15px;background:var(--surface);color:var(--text);font-family:inherit;-webkit-appearance:none}
.field input:focus,.field select:focus{outline:2px solid var(--green);border-color:var(--green)}
.pbtn{width:100%;padding:13px;border-radius:12px;background:var(--green);border:none;color:#fff;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;margin-top:4px}
.pbtn:active{opacity:.85;transform:scale(.98)}
.dbtn{width:100%;background:none;border:none;color:var(--red);font-size:13px;cursor:pointer;padding:12px 0;font-family:inherit;text-align:center}
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#1a1a18;color:#fff;padding:10px 20px;border-radius:20px;font-size:13px;z-index:200;opacity:0;transition:opacity .3s;pointer-events:none;white-space:nowrap}.toast.show{opacity:1}
.scbig{font-size:54px;font-weight:700;color:#EF9F27;line-height:1}
/* History */
.hday-card{background:var(--surface);border:0.5px solid var(--border);border-radius:var(--r);padding:14px 16px;margin-bottom:10px;cursor:pointer}
.hday-card:active{opacity:.8}
.hday-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.hday-date{font-size:14px;font-weight:600}.hday-sub{font-size:12px;color:var(--text3)}
.hday-pills{display:flex;gap:6px;flex-wrap:wrap}
.hpill{font-size:11px;padding:3px 8px;border-radius:20px;background:var(--bg);color:var(--text2);border:0.5px solid var(--border)}
.hpill.good{background:var(--green-bg);color:var(--green-text);border-color:var(--green)}
.hpill.warn{background:var(--orange-bg);color:var(--orange-text);border-color:var(--orange)}
.habit-done-row{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:0.5px solid var(--border)}.habit-done-row:last-child{border-bottom:none}
.habit-done-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-inner">
    <div><div class="greeting" id="greetTxt">Hello</div><div class="date-lbl" id="dateTxt"></div></div>
    <div class="streak-pill"><i class="ti ti-flame" style="font-size:15px;color:#EF9F27"></i><span class="streak-num" id="masterNum">0</span><span class="streak-lbl">day streak</span></div>
  </div>
</div>
<div class="body" id="bodyEl">

  <!-- HOME -->
  <div id="tab-home" class="tab active">
    <div style="height:8px"></div>
    <div class="slbl">quick log</div>
    <div class="g2">
      <div class="qc" id="qc-water">
        <div class="qc-top"><span class="qc-lbl"><i class="ti ti-droplet" style="font-size:13px"></i> Water</span><span style="font-size:10px;color:var(--text3)" id="water-status">0/8</span></div>
        <div class="crow">
          <button class="cbtn" onclick="adjustWater(-1)">−</button>
          <div><div class="cval" id="q-water">0</div><div class="cunit">glasses</div></div>
          <button class="cbtn" onclick="adjustWater(1)">+</button>
        </div>
        <div class="bar"><div class="bf" id="water-bar" style="width:0%"></div></div>
      </div>
      <div class="qc" id="qc-sleep">
        <div class="qc-top"><span class="qc-lbl"><i class="ti ti-moon" style="font-size:13px"></i> Sleep</span><button class="lbtn" onclick="openSheet('sleep')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div>
        <div class="qc-val" id="q-sleep">—</div><div class="qc-unit" id="q-sleep-unit">hrs last night</div>
      </div>
      <div class="qc" id="qc-steps">
        <div class="qc-top"><span class="qc-lbl"><i class="ti ti-run" style="font-size:13px"></i> Steps</span><button class="lbtn" onclick="openSheet('steps')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div>
        <div class="qc-val" id="q-steps">—</div><div class="qc-unit" id="q-steps-unit">steps today</div>
      </div>
      <div class="qc" id="qc-spend">
        <div class="qc-top"><span class="qc-lbl"><i class="ti ti-coin" style="font-size:13px"></i> Spent</span><button class="lbtn" onclick="openSheet('spend')"><i class="ti ti-plus" style="font-size:11px"></i> log</button></div>
        <div class="qc-val" id="q-spend">$0</div><div class="qc-unit">today</div>
      </div>
    </div>
    <div class="slbl">today's habits</div>
    <div class="card" id="home-habits"></div>
    <div class="slbl">goals</div>
    <div class="card" id="home-goals"></div>
  </div>

  <!-- HISTORY -->
  <div id="tab-history" class="tab">
    <div style="height:8px"></div>
    <div class="slbl">past days</div>
    <div id="history-list"><div class="empty">Loading history...</div></div>
  </div>

  <!-- MONEY -->
  <div id="tab-money" class="tab">
    <div style="height:8px"></div>
    <div class="sgrid">
      <div class="sbox"><div class="sval" id="m-today">$0</div><div class="slb">spent today</div></div>
      <div class="sbox"><div class="sval" id="m-week">$0</div><div class="slb">this week</div></div>
    </div>
    <div class="slbl">today's expenses</div>
    <div class="card"><div id="m-log"></div><button class="addbtn" onclick="openSheet('spend')"><i class="ti ti-plus" style="font-size:14px"></i> add expense</button></div>
  </div>

  <!-- GOALS -->
  <div id="tab-goals" class="tab">
    <div style="height:8px"></div>
    <div class="slbl">my goals</div>
    <div class="card" id="g-goals"></div>
    <button class="addbtn" onclick="openSheet('addGoal')"><i class="ti ti-plus" style="font-size:14px"></i> add goal</button>
    <div style="height:16px"></div>
    <div class="slbl">habits</div>
    <div class="card" id="g-habits"></div>
    <button class="addbtn" onclick="openSheet('addHabit')"><i class="ti ti-plus" style="font-size:14px"></i> add habit</button>
  </div>

  <!-- YOU -->
  <div id="tab-you" class="tab">
    <div style="height:8px"></div>
    <div class="slbl">your streak</div>
    <div class="card" style="text-align:center;padding:24px">
      <div class="scbig" id="s-streakBig">0</div>
      <div style="font-size:13px;color:var(--amber-text);margin-top:4px;font-weight:500">days in a row</div>
      <div style="font-size:13px;color:var(--text2);margin-top:8px;line-height:1.5">Complete <strong>every habit</strong> each day.<br>Miss one and it resets to zero.</div>
    </div>
    <div class="slbl" style="margin-top:16px">settings</div>
    <div class="card">
      <div class="srow" onclick="openSheet('rename')"><div><div class="sl">Your name</div><div class="ss" id="s-name">Tap to set</div></div><i class="ti ti-chevron-right" style="font-size:16px;color:var(--text3)"></i></div>
      <div class="srow" onclick="openSheet('waterGoal')"><div><div class="sl">Daily water goal</div><div class="ss" id="s-waterGoal">8 glasses</div></div><i class="ti ti-chevron-right" style="font-size:16px;color:var(--text3)"></i></div>
    </div>
    <div class="slbl" style="margin-top:16px">data</div>
    <div class="card">
      <div class="srow" onclick="doReset()"><div><div class="sl" style="color:var(--red)">Reset all data</div><div class="ss">Cannot be undone</div></div><i class="ti ti-trash" style="font-size:16px;color:var(--red)"></i></div>
    </div>
  </div>
</div>

<nav class="nav">
  <button class="nb active" onclick="switchTab('home',this)"><i class="ti ti-home"></i><span>Home</span></button>
  <button class="nb" onclick="switchTab('history',this);loadHistory()"><i class="ti ti-calendar"></i><span>History</span></button>
  <button class="nb" onclick="switchTab('money',this)"><i class="ti ti-coin"></i><span>Money</span></button>
  <button class="nb" onclick="switchTab('goals',this)"><i class="ti ti-target"></i><span>Goals</span></button>
  <button class="nb" onclick="switchTab('you',this)"><i class="ti ti-user"></i><span>You</span></button>
</nav>

<div class="overlay" id="overlay" onclick="overlayClick(event)">
  <div class="sheet"><div class="shandle"></div><div id="sheetContent"></div></div>
</div>
<div class="toast" id="toast"></div>

<script>
let S={},D={},TODAY='',sheetType='',sheetId=null;

async function fetchData(){
  try{
    const r=await fetch('/api/data');
    const j=await r.json();
    S=j.settings; D=j.day; TODAY=j.today;
    renderAll();
  }catch(e){console.error(e);}
}

async function persistDay(){
  try{await fetch('/api/save_day',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({date:TODAY,data:D})});}
  catch(e){console.error('Save day failed',e);}
}
async function persistSettings(){
  try{await fetch('/api/save_settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(S)});}
  catch(e){console.error('Save settings failed',e);}
}

function adjustWater(delta){
  D.water=Math.max(0,Math.min(30,(D.water||0)+delta));
  persistDay(); updateWaterCard();
}

function updateWaterCard(){
  const w=D.water||0,goal=S.water_goal||8;
  document.getElementById('q-water').textContent=w;
  document.getElementById('water-status').textContent=w+'/'+goal;
  const pct=Math.min(w/goal*100,100);
  const bar=document.getElementById('water-bar'),card=document.getElementById('qc-water');
  card.className='qc'+(w>=goal?' sg':'');
  bar.style.background=w>=goal?'var(--green)':'var(--blue)';
  bar.style.width=pct+'%';
}

function updateSleepCard(){
  const card=document.getElementById('qc-sleep'),valEl=document.getElementById('q-sleep'),unitEl=document.getElementById('q-sleep-unit');
  card.className='qc';
  if(!D.sleep){valEl.textContent='—';unitEl.textContent='hrs last night';return;}
  const v=parseFloat(D.sleep);valEl.textContent=v.toFixed(1);
  if(v>=7){card.classList.add('sg');unitEl.textContent='✓ great sleep!';}
  else if(v>=5){unitEl.textContent='hrs — could be more';}
  else{card.classList.add('so');unitEl.textContent='hrs — rest up!';}
}

function updateStepsCard(){
  const card=document.getElementById('qc-steps'),valEl=document.getElementById('q-steps'),unitEl=document.getElementById('q-steps-unit');
  card.className='qc';
  if(D.steps==null){valEl.textContent='—';unitEl.textContent='steps today';return;}
  const v=D.steps;valEl.textContent=Number(v).toLocaleString();
  if(v>=10000){card.classList.add('sbg');unitEl.textContent='🔥 amazing!';}
  else if(v>=7000){card.classList.add('sg');unitEl.textContent='✓ great job!';}
  else if(v>=1000){card.classList.add('so');unitEl.textContent='steps — keep going!';}
}

function renderAll(){
  const h=new Date().getHours(),name=S.name?', '+S.name:'';
  document.getElementById('greetTxt').textContent=(h<12?'Good morning':h<17?'Good afternoon':'Good evening')+name;
  document.getElementById('dateTxt').textContent=new Date().toLocaleDateString('en-AU',{weekday:'long',day:'numeric',month:'long'});
  document.getElementById('masterNum').textContent=S.master_streak||0;
  document.getElementById('s-streakBig').textContent=S.master_streak||0;
  document.getElementById('s-name').textContent=S.name||'Tap to set';
  document.getElementById('s-waterGoal').textContent=(S.water_goal||8)+' glasses';
  renderHome(); renderMoney(); renderGoalsPage();
}

function renderHome(){
  updateWaterCard(); updateSleepCard(); updateStepsCard();
  document.getElementById('q-spend').textContent='$'+Math.round(D.spend_today||0);
  const done=D.habits_done||[];
  document.getElementById('home-habits').innerHTML=(S.habits||[]).length?
    S.habits.map(h=>{const isDone=done.includes(h.id);return`<div class="hrow">
      <button class="hchk${isDone?' done':''}" onclick="toggleHabit(${h.id})">${isDone?'<i class="ti ti-check" style="font-size:13px;color:#fff"></i>':''}</button>
      <span class="hname">${h.name}</span>
      <span class="hstr${h.streak>=3?' hot':''}"><i class="ti ti-flame" style="font-size:12px"></i> ${h.streak||0}d</span>
    </div>`;}).join(''):'<div class="empty">No habits yet</div>';
  document.getElementById('home-goals').innerHTML=(S.goals||[]).length?
    S.goals.map(g=>{const pct=Math.min(Math.round(g.current/g.target*100),100),col=pct>=80?'var(--green)':pct>=40?'var(--blue)':'var(--amber)';
    return`<div class="grow"><div class="gtop"><span class="gname">${g.name}</span><span class="gpct">${pct}%</span></div>
    <div class="gsub">${g.current}/${g.target} ${g.unit}</div>
    <div class="bar"><div class="bf" style="width:${pct}%;background:${col}"></div></div></div>`;}).join('')
    :'<div class="empty">No goals yet</div>';
}

function renderMoney(){
  document.getElementById('m-today').textContent='$'+Math.round(D.spend_today||0);
  const logs=D.spend_log||[],now=Date.now(),week=(D.spend_log||[]).reduce((a,e)=>a+e.amt,0);
  document.getElementById('m-week').textContent='$'+Math.round(week);
  const logEl=document.getElementById('m-log');
  logEl.innerHTML=logs.length?logs.slice().reverse().map(e=>`<div class="lrow">
    <div><div class="ldesc">${e.desc}</div><div class="lsub">${e.cat}</div></div>
    <span class="lamt">$${parseFloat(e.amt).toFixed(2)}</span>
  </div>`).join(''):'<div class="empty">No expenses yet</div>';
}

function renderGoalsPage(){
  document.getElementById('g-goals').innerHTML=(S.goals||[]).length?
    S.goals.map(g=>{const pct=Math.min(Math.round(g.current/g.target*100),100),col=pct>=80?'var(--green)':pct>=40?'var(--blue)':'var(--amber)';
    return`<div class="grow"><div class="gtop"><span class="gname">${g.name}</span>
    <div class="gact"><span class="gpct">${pct}%</span>
    <button class="lbtn" onclick="openSheet('updateGoal',${g.id})"><i class="ti ti-pencil" style="font-size:11px"></i> update</button>
    <button class="lbtn" onclick="deleteGoal(${g.id})" style="color:var(--red)"><i class="ti ti-trash" style="font-size:11px"></i></button>
    </div></div><div class="gsub">${g.current}/${g.target} ${g.unit}</div>
    <div class="bar"><div class="bf" style="width:${pct}%;background:${col}"></div></div></div>`;}).join('')
    :'<div class="empty">No goals yet!</div>';
  document.getElementById('g-habits').innerHTML=(S.habits||[]).length?
    S.habits.map(h=>{const isDone=(D.habits_done||[]).includes(h.id);return`<div class="hrow">
      <button class="hchk${isDone?' done':''}" onclick="toggleHabit(${h.id})">${isDone?'<i class="ti ti-check" style="font-size:13px;color:#fff"></i>':''}</button>
      <span class="hname">${h.name}</span>
      <div style="display:flex;align-items:center;gap:8px">
        <span class="hstr${h.streak>=3?' hot':''}"><i class="ti ti-flame" style="font-size:12px"></i> ${h.streak||0}d</span>
        <button class="lbtn" onclick="deleteHabit(${h.id})" style="color:var(--red)"><i class="ti ti-trash" style="font-size:11px"></i></button>
      </div></div>`;}).join(''):'<div class="empty">No habits yet</div>';
}

async function loadHistory(){
  const el=document.getElementById('history-list');
  el.innerHTML='<div class="empty">Loading...</div>';
  const r=await fetch('/api/history');
  const days=await r.json();
  if(!days.length){el.innerHTML='<div class="empty">No history yet — come back tomorrow!</div>';return;}
  el.innerHTML=days.map(d=>{
    const dt=new Date(d.date+'T12:00:00');
    const label=dt.toLocaleDateString('en-AU',{weekday:'long',day:'numeric',month:'short'});
    const isToday=d.date===TODAY;
    const doneCnt=(d.habits_done||[]).length,totalCnt=(S.habits||[]).length;
    const allDone=doneCnt===totalCnt&&totalCnt>0;
    return`<div class="hday-card" onclick="openDayDetail('${d.date}')">
      <div class="hday-top">
        <div><div class="hday-date">${isToday?'Today':label}</div><div class="hday-sub">${doneCnt}/${totalCnt} habits · ${d.sleep?d.sleep+'hrs sleep':'no sleep logged'}</div></div>
        <span class="bdg ${allDone?'bg':'ba'}">${allDone?'✓ Perfect':'You can do better Rik'}</span>
      </div>
      <div class="hday-pills">
        ${d.water?`<span class="hpill${d.water>=(S.water_goal||8)?' good':''}">${d.water} glasses</span>`:''}
        ${d.steps?`<span class="hpill${d.steps>=7000?' good':d.steps>=1000?' warn':''}">${Number(d.steps).toLocaleString()} steps</span>`:''}
        ${d.spend_today?`<span class="hpill">$${Math.round(d.spend_today)} spent</span>`:''}
      </div>
    </div>`;
  }).join('');
}

function openDayDetail(dateStr){
  fetch('/api/history').then(r=>r.json()).then(days=>{
    const d=days.find(x=>x.date===dateStr);
    if(!d)return;
    const dt=new Date(dateStr+'T12:00:00');
    const label=dt.toLocaleDateString('en-AU',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
    const c=document.getElementById('sheetContent');
    const habitsHTML=(S.habits||[]).map(h=>{
      const done=(d.habits_done||[]).includes(h.id);
      return`<div class="habit-done-row">
        <div class="habit-done-dot" style="background:${done?'var(--green)':'var(--border2)'}"></div>
        <span style="font-size:14px;color:${done?'var(--text)':'var(--text3)'}">${h.name}</span>
        ${done?'<span style="margin-left:auto;font-size:11px;color:var(--green-text)">done</span>':''}
      </div>`;}).join('');
    const spendHTML=(d.spend_log||[]).length?d.spend_log.map(e=>`<div class="lrow"><div><div class="ldesc">${e.desc}</div><div class="lsub">${e.cat}</div></div><span class="lamt">$${parseFloat(e.amt).toFixed(2)}</span></div>`).join(''):'<div style="font-size:13px;color:var(--text3);padding:8px 0">No expenses</div>';
    c.innerHTML=`<div class="stitle">${label}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px">
        <div style="background:var(--bg);border-radius:10px;padding:10px"><div style="font-size:20px;font-weight:600">${d.sleep?d.sleep+'hrs':'—'}</div><div style="font-size:11px;color:var(--text3)">sleep</div></div>
        <div style="background:var(--bg);border-radius:10px;padding:10px"><div style="font-size:20px;font-weight:600">${d.water||0}</div><div style="font-size:11px;color:var(--text3)">glasses water</div></div>
        <div style="background:var(--bg);border-radius:10px;padding:10px"><div style="font-size:20px;font-weight:600">${d.steps?Number(d.steps).toLocaleString():'—'}</div><div style="font-size:11px;color:var(--text3)">steps</div></div>
        <div style="background:var(--bg);border-radius:10px;padding:10px"><div style="font-size:20px;font-weight:600">$${Math.round(d.spend_today||0)}</div><div style="font-size:11px;color:var(--text3)">spent</div></div>
      </div>
      <div style="font-size:11px;font-weight:600;color:var(--text3);letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Habits</div>
      <div style="margin-bottom:16px">${habitsHTML}</div>
      <div style="font-size:11px;font-weight:600;color:var(--text3);letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">Expenses</div>
      ${spendHTML}`;
    document.getElementById('overlay').classList.add('open');
  });
}

function toggleHabit(id){
  if(!D.habits_done)D.habits_done=[];
  const idx=D.habits_done.indexOf(id);
  if(idx>-1)D.habits_done.splice(idx,1);
  else D.habits_done.push(id);
  persistDay(); renderAll();
}

function deleteGoal(id){S.goals=S.goals.filter(g=>g.id!==id);persistSettings();renderAll();}
function deleteHabit(id){S.habits=S.habits.filter(h=>h.id!==id);persistSettings();renderAll();}

function openSheet(type,id=null){
  sheetType=type;sheetId=id;
  const c=document.getElementById('sheetContent');
  if(type==='sleep'){c.innerHTML=`<div class="stitle">Log sleep</div><div class="field"><label>Hours slept last night</label><input type="number" id="si" min="0" max="24" step="0.5" value="${D.sleep||7}"></div><button class="pbtn" onclick="doSave()">Save</button>`;}
  else if(type==='steps'){c.innerHTML=`<div class="stitle">Log steps</div><div class="field"><label>Steps today</label><input type="number" id="si" min="0" step="100" value="${D.steps||0}"></div><button class="pbtn" onclick="doSave()">Save</button>`;}
  else if(type==='spend'){c.innerHTML=`<div class="stitle">Add expense</div><div class="field"><label>Amount ($)</label><input type="number" id="sa" min="0" step="0.5" value="0"></div><div class="field"><label>Description</label><input type="text" id="sd" placeholder="Coffee, groceries..."></div><div class="field"><label>Category</label><select id="sc"><option>Food & drink</option><option>Transport</option><option>Shopping</option><option>Health</option><option>Entertainment</option><option>Other</option></select></div><button class="pbtn" onclick="doSave()">Save</button>`;}
  else if(type==='addGoal'){c.innerHTML=`<div class="stitle">Add goal</div><div class="field"><label>Goal name</label><input type="text" id="gn" placeholder="Save $5,000..."></div><div class="field"><label>Current progress</label><input type="number" id="gc" min="0" value="0"></div><div class="field"><label>Target</label><input type="number" id="gt" min="1" value="100"></div><div class="field"><label>Unit ($, km, books...)</label><input type="text" id="gu" placeholder="books"></div><button class="pbtn" onclick="doSave()">Add goal</button>`;}
  else if(type==='updateGoal'){const g=S.goals.find(g=>g.id===id);c.innerHTML=`<div class="stitle">Update: ${g.name}</div><div class="field"><label>Current progress</label><input type="number" id="gu2" min="0" value="${g.current}"></div><div class="field"><label>New target</label><input type="number" id="gt2" min="1" value="${g.target}"></div><button class="pbtn" onclick="doSave()">Save</button><button class="dbtn" onclick="deleteGoal(${id});closeSheet()">Delete this goal</button>`;}
  else if(type==='addHabit'){c.innerHTML=`<div class="stitle">Add habit</div><div class="field"><label>Habit name</label><input type="text" id="hn" placeholder="Morning run, Meditate..."></div><button class="pbtn" onclick="doSave()">Add habit</button>`;}
  else if(type==='rename'){c.innerHTML=`<div class="stitle">Your name</div><div class="field"><label>What should I call you?</label><input type="text" id="rn" value="${S.name||''}" placeholder="Your name"></div><button class="pbtn" onclick="doSave()">Save</button>`;}
  else if(type==='waterGoal'){c.innerHTML=`<div class="stitle">Daily water goal</div><div class="field"><label>Glasses per day</label><input type="number" id="wg" min="1" max="20" value="${S.water_goal||8}"></div><button class="pbtn" onclick="doSave()">Save</button>`;}
  document.getElementById('overlay').classList.add('open');
  setTimeout(()=>{const f=document.querySelector('#sheetContent input,#sheetContent select');if(f)f.focus();},200);
}

function doSave(){
  const t=sheetType;
  if(t==='sleep'){const v=parseFloat(document.getElementById('si').value);if(!isNaN(v)&&v>0){D.sleep=Math.round(v*10)/10;toast('Sleep logged!');}}
  else if(t==='steps'){const v=parseInt(document.getElementById('si').value);if(!isNaN(v))D.steps=Math.max(0,v);toast('Steps logged!');}
  else if(t==='spend'){const a=parseFloat(document.getElementById('sa').value),desc=document.getElementById('sd').value||'Expense',cat=document.getElementById('sc').value;if(!isNaN(a)&&a>0){D.spend_today=Math.round((D.spend_today+a)*100)/100;if(!D.spend_log)D.spend_log=[];D.spend_log.push({amt:a,desc,cat});toast('Expense added!');}}
  else if(t==='addGoal'){const n=document.getElementById('gn').value.trim(),c=parseFloat(document.getElementById('gc').value)||0,tg=parseFloat(document.getElementById('gt').value)||100,u=document.getElementById('gu').value.trim()||'';if(n){if(!S.goals)S.goals=[];S.goals.push({id:Date.now(),name:n,current:c,target:tg,unit:u});toast('Goal added!');}}
  else if(t==='updateGoal'){const g=S.goals.find(g=>g.id===sheetId);if(g){g.current=parseFloat(document.getElementById('gu2').value)||0;g.target=parseFloat(document.getElementById('gt2').value)||g.target;toast('Goal updated!');}}
  else if(t==='addHabit'){const n=document.getElementById('hn').value.trim();if(n){if(!S.habits)S.habits=[];S.habits.push({id:Date.now(),name:n,streak:0});toast('Habit added!');}}
  else if(t==='rename'){S.name=document.getElementById('rn').value.trim();persistSettings();toast('Saved!');}
  else if(t==='waterGoal'){const v=parseInt(document.getElementById('wg').value);if(!isNaN(v)&&v>0){S.water_goal=v;persistSettings();}toast('Updated!');}
  if(['sleep','steps','spend'].includes(t))persistDay();
  if(['addGoal','updateGoal','addHabit'].includes(t))persistSettings();
  renderAll(); closeSheet();
}

function closeSheet(){document.getElementById('overlay').classList.remove('open');}
function overlayClick(e){if(e.target===document.getElementById('overlay'))closeSheet();}
async function doReset(){if(!confirm('Reset ALL data?'))return;const r=await fetch('/api/reset',{method:'POST'});const j=await r.json();S=j.settings;D=j.day;TODAY=j.today;renderAll();toast('Reset!');}
function switchTab(name,btn){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.nb').forEach(b=>b.classList.remove('active'));document.getElementById('tab-'+name).classList.add('active');btn.classList.add('active');document.getElementById('bodyEl').scrollTop=0;}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000);}

fetchData();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

@app.route("/api/data")
def api_data():
    settings = load_settings()
    day = get_today_data(settings)
    return jsonify({"settings": settings, "day": day, "today": today()})

@app.route("/api/save_day", methods=["POST"])
def api_save_day():
    body = request.json
    save_day(body["date"], body["data"])
    return jsonify({"ok": True})

@app.route("/api/save_settings", methods=["POST"])
def api_save_settings():
    save_settings(request.json)
    return jsonify({"ok": True})

@app.route("/api/history")
def api_history():
    return jsonify(load_history(60))

@app.route("/api/reset", methods=["POST"])
def api_reset():
    s = default_settings()
    save_settings(s)
    d = default_day(s)
    save_day(today(), d)
    return jsonify({"settings": s, "day": d, "today": today()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n✅  Life Dashboard running! http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)