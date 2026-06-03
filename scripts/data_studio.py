#!/usr/bin/env python3
"""OneTag HMAS — Data Studio (SQLite). Full web-based database GUI."""

import sqlite3, json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

DB_PATH = "/workspace/forrest-plan-and-track/data/onetag.db"
PORT = 8765

def query(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute(sql)
        rows = [dict(r) for r in c.fetchall()]
        cols = [d[0] for d in c.description] if c.description else []
        return cols, rows, None
    except Exception as e:
        return [], [], str(e)
    finally:
        conn.close()

class H(SimpleHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(p.query)
        if p.path == "/":
            self.send(200, "text/html", PAGE)
        elif p.path == "/api/tables":
            _, rows, _ = query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            # Get counts one by one (fast for small tables)
            result = []
            for r in rows:
                name = r['name']
                _, cnt, _ = query(f'SELECT COUNT(*) as c FROM "{name}"')
                _, info, _ = query(f'PRAGMA table_info("{name}")')
                result.append({"name": name, "rows": cnt[0]['c'] if cnt else 0, "cols": len(info)})
            self.send(200, "application/json", json.dumps(result, default=str))
        elif p.path == "/api/data":
            t = q.get("t", [""])[0]
            page = int(q.get("p", [0])[0])
            lim = 50; off = lim * page
            c, r, e = query(f'SELECT * FROM "{t}" LIMIT {lim} OFFSET {off}')
            _, cnt, _ = query(f'SELECT COUNT(*) as c FROM "{t}"')
            self.send(200, "application/json", json.dumps({"cols": c, "rows": r, "total": cnt[0]['c'] if cnt else 0, "page": lim, "error": e}, default=str))
        elif p.path == "/api/schema":
            t = q.get("t", [""])[0]
            _, r, e = query(f'PRAGMA table_info("{t}")')
            _, fk, _ = query(f'PRAGMA foreign_key_list("{t}")')
            self.send(200, "application/json", json.dumps({"rows": r, "fks": fk, "error": e}, default=str))
        elif p.path == "/api/sql":
            sql = urllib.parse.unquote(q.get("q", [""])[0])
            c, r, e = query(sql)
            self.send(200, "application/json", json.dumps({"cols": c, "rows": r, "count": len(r), "error": e}, default=str))
        else:
            self.send(404, "text/plain", "Not found")
    
    def send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)
    
    def log_message(self, *a): pass

PAGE = open(__file__.replace('.py', '.html')).read() if __file__.replace('.py', '.html') else ""

# Inline HTML page
PAGE = r"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>OneTag HMAS — Data Studio</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden;font-size:13px}
#sb{width:280px;background:#161b22;border-right:1px solid #21262d;display:flex;flex-direction:column}
#sb h3{padding:10px;color:#58a6ff;font-size:12px;border-bottom:1px solid #21262d}
#srch{padding:6px;border-bottom:1px solid #21262d}
#srch input{width:100%;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:5px 8px;border-radius:4px;font-size:11px}
#tl{flex:1;overflow-y:auto}
.ti{padding:6px 10px;cursor:pointer;border-bottom:1px solid #1c2122;display:flex;justify-content:space-between;font-size:11px}
.ti:hover{background:#1c2128}.ti.sel{background:#1a3a5c}
.tn{color:#e6edf3}.tm{color:#6e7681;font-size:10px}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#tb{padding:6px 10px;background:#161b22;border-bottom:1px solid #21262d;display:flex;gap:5px;align-items:center}
#tb button{background:#238636;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px}
#tb button.sec{background:#30363d}
#sql{flex:0 0 100px;border-bottom:1px solid #21262d;position:relative}
#sql textarea{width:100%;height:100%;background:transparent;color:#c9d1d9;border:none;padding:8px;font-size:12px;font-family:'SF Mono',monospace;resize:none;outline:none}
#run{position:absolute;bottom:6px;right:6px;background:#238636;color:#fff;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:11px}
#tabs{display:flex;border-bottom:1px solid #21262d}
.tab{padding:6px 14px;cursor:pointer;font-size:11px;color:#8b949e}
.tab.on{color:#58a6ff;border-bottom:2px solid #58a6ff}
#results{flex:1;overflow:auto}
.rtable{width:100%;border-collapse:collapse;font-size:11px}
.rtable th{background:#161b22;color:#58a6ff;padding:5px 8px;text-align:left;border-bottom:1px solid #30363d;position:sticky;top:0;white-space:nowrap}
.rtable td{padding:3px 8px;border-bottom:1px solid #1c262d;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rtable tr:hover td{background:#1c2128}
.pg{padding:6px 10px;display:flex;gap:6px;align-items:center}
.pg a{color:#58a6ff;text-decoration:none;padding:2px 6px;background:#161b22;border-radius:3px;font-size:10px}
.pg sp{color:#6e7681;font-size:10px}
.err{color:#f85149;padding:12px}
.sc-row{display:flex;gap:8px;padding:3px 0;border-bottom:1px solid #1c2122;font-size:11px}
.sc-col{color:#79c0ff;min-width:140px}
.sc-pk{color:#f0883e;font-weight:bold}
.sc-fk{color:#58a6ff}
</style></head><body>
<div id="sb"><h3>📋 Tables</h3><div id="srch"><input id="sq" placeholder="Search..." oninput="ft()"></div><div id="tl"></div></div>
<div id="main">
<div id="tb">
<button onclick="run()">▶ Run</button>
<button class="sec" onclick="document.getElementById('sq2').value=''">Clear</button>
<span id="st" style="font-size:10px;color:#6e7681;flex:1;text-align:right"></span>
</div>
<div id="sql"><textarea id="sq2" placeholder="SELECT * FROM Users LIMIT 10"></textarea><button id="run" onclick="run()">▶</button></div>
<div id="tabs"><div class="tab on" onclick="tab(this,'d')">Data</div><div class="tab" onclick="tab(this,'s')">Schema</div></div>
<div id="results"></div>
</div>
<script>
let cur=null,p=0;
const $=id=>document.getElementById(id);
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

function load(){
  fetch('/api/tables').then(r=>r.json()).then(d=>{
    d.sort((a,b)=>b.rows-a.rows);
    $('tl').innerHTML=d.map(t=>`<div class="ti" onclick="sel(this,'${t.name}')"><span class="tn">${esc(t.name)}</span><span class="tm">${t.rows.toLocaleString()} · ${t.cols}</span></div>`).join('');
    if(d.length) $('tl').querySelector('.ti').click();
  });
}

function sel(el,name){
  document.querySelectorAll('.ti').forEach(e=>e.classList.remove('sel'));
  el.classList.add('sel'); cur=name; p=0; loadData(); loadSchema();
}

function loadData(){
  fetch(`/api/data?t=${encodeURIComponent(cur)}&p=${p}`).then(r=>r.json()).then(d=>{
    if(d.error){ $('results').innerHTML=`<div class="err">${esc(d.error)}</div>`; return; }
    let h='<table class="rtable"><tr>'+(d.cols||[]).map(c=>`<th>${esc(c)}</th>`).join('')+'</tr>';
    d.rows.forEach(r=>{h+='<tr>'+(d.cols||[]).map(c=>`<td>${r[c]!==null?esc(String(r[c])):'<em style="color:#6e7681">null</em>'}</td>`).join('')+'</tr>';});
    let tot=d.total||0,pg=Math.ceil(tot/50);
    h+=`</table><div class="pg">${p>0?`<a href="#"onclick="pp(p-1);return false">←</a>':''}<span>${p+1}/${pg} · ${tot.toLocaleString()} rows</span>${p<pg-1?`<a href="#"onclick="pp(p+1);return false">→</a>':''}</div>`;
    $('results').innerHTML=h; $('st').textContent=`${tot.toLocaleString()} rows`;
  });
}

function loadSchema(){
  fetch(`/api/schema?t=${encodeURIComponent(cur)}`).then(r=>r.json()).then(d=>{
    let h='';
    d.rows.forEach(c=>{
      let t=[]; if(c.pk) t.push('<span class="sc-pk">🔑</span>'); t.push(c.type||'TEXT'); if(!c.notnull) t.push('NULL');
      h+=`<div class="sc-row"><span class="sc-col">${esc(c.name)}</span><span>${t.join(' ')}</span></div>`;
    });
    if(d.fks&&d.fks.length){
      h+='<div style="margin-top:6px;color:#58a6ff">Foreign Keys</div>';
      d.fks.forEach(f=>{h+=`<div class="sc-row"><span class="sc-fk">${esc(f.from)}</span> → <span class="sc-fk">${esc(f.table)}.${esc(f.to)}</span></div>`;});
    }
    $('results').setAttribute('data-schema',h);
  });
}

function tab(el,name){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on')); el.classList.add('on');
  if(name==='s'){let s=$('results').getAttribute('data-schema');$('results').innerHTML=s||'';}else{loadData();}
}

function run(){
  let sql=$('sq2').value.trim(); if(!sql) return;
  $('st').textContent='Running...';
  fetch(`/api/sql?q=${encodeURIComponent(sql)}`).then(r=>r.json()).then(d=>{
    if(d.error){$('results').innerHTML=`<div class="err">${esc(d.error)}</div>`;$('st').textContent='Error';return;}
    let h='<table class="rtable"><tr>'+(d.cols||[]).map(c=>`<th>${esc(c)}</th>`).join('')+'</tr>';
    d.rows.forEach(r=>{h+='<tr>'+(d.cols||[]).map(c=>`<td>${r[c]!==null?esc(String(r[c])):'<em style="color:#6e7681">null</em>'}</td>`).join('')+'</tr>';});
    h+='</table>'; $('results').innerHTML=h; $('st').textContent=`${d.count} rows`;
  });
}
function pp(n){p=n;loadData();}
function ft(){let q=$('sq').value.toLowerCase();document.querySelectorAll('.ti').forEach(el=>{el.style.display=el.querySelector('.tn').textContent.toLowerCase().includes(q)?'':'none';});}
$('sq2').addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter')run();});
load();
</script></body></html>"""

if __name__=="__main__":
    print(f"OneTag Data Studio — http://localhost:{PORT}")
    HTTPServer(("0.0.0.0",PORT),H).serve_forever()
