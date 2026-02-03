import os
import psycopg2
from flask import Flask, render_template_string, request, session, redirect, jsonify

app = Flask(__name__)
app.secret_key = "MB_CLASH_ULTRA_MASTER_KEY"

# Configurações de Ambiente (Koyeb/Neon/MercadoPago)
DATABASE_URL = os.environ.get("DATABASE_URL")
MP_TOKEN = os.environ.get("MP_ACCESS_TOKEN")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Interface de Alta Performance (CSS/JS Otimizado)
ARENA_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>MB CLASH - High Performance</title>
    <style>
        :root { --neon: #4ecca3; --danger: #ff4b2b; --gold: #ffd700; }
        body { margin: 0; background: #05050a; color: #eee; font-family: 'Segoe UI', sans-serif; overflow: hidden; }
        
        /* HUD - Consumo Zero de GPU */
        .hud { position: fixed; top: 0; width: 100%; height: 60px; background: rgba(0,0,0,0.85); display: flex; justify-content: space-around; align-items: center; border-bottom: 2px solid var(--neon); z-index: 100; font-size: 0.9rem; }
        
        /* Arena com Parallax Suave */
        #arena { width: 100vw; height: 65vh; background: #111 url('https://imgur.com/vH6ZzV6.png') center/cover; position: relative; }
        
        /* Herói com Aceleração de Hardware */
        #player { 
            width: 70px; height: 70px; 
            background: url('{{ hero_img }}') no-repeat center; 
            background-size: contain; position: absolute; 
            transform: translate3d(50px, -50px, 0); /* Ultra Performance */
            will-change: transform; transition: transform 0.05s linear; 
        }

        /* Painel de Comando */
        .controls { height: 35vh; background: #0f0f1a; display: grid; grid-template-columns: 1fr 1fr; align-items: center; padding: 10px; }
        .d-pad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .action-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
        
        .btn { padding: 15px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; color: #fff; text-transform: uppercase; }
        .move { background: #16213e; border: 1px solid var(--neon); }
        .atk { background: var(--danger); box-shadow: 0 0 15px var(--danger); }
        .rec { background: var(--gold); color: #000; }
    </style>
</head>
<body>
    <div class="hud">
        <span>⚔️ {{ user }} (LV {{ lvl }})</span>
        <span style="color: var(--gold)">💰 R$ {{ "%.2f"|format(saldo) }}</span>
    </div>

    <div id="arena"><div id="player"></div></div>

    <div class="controls">
        <div class="d-pad">
            <button class="btn move" onmousedown="mMove('L')">◀</button>
            <button class="btn move" onclick="mJump()">🚀</button>
            <button class="btn move" onmousedown="mMove('R')">▶</button>
        </div>
        <div class="action-grid">
            <button class="btn atk" onclick="mAtk()">ATACAR (VS)</button>
            <button class="btn rec" onclick="window.location.href='/loja'">RECARGA PIX</button>
        </div>
    </div>

    <script>
        let x = 50; let y = -50;
        const p = document.getElementById('player');
        
        function update() { p.style.transform = `translate3d(${x}px, ${y}px, 0)`; }
        function mMove(d) { x += (d === 'R' ? 30 : -30); update(); }
        function mJump() { y = -150; update(); setTimeout(() => { y = -50; update(); }, 300); }
        function mAtk() { p.style.filter = 'brightness(3)'; setTimeout(() => p.style.filter = 'none', 100); }
        
        document.addEventListener('keydown', (e) => {
            if(e.key === 'ArrowRight') mMove('R');
            if(e.key === 'ArrowLeft') mMove('L');
            if(e.key === ' ') mJump();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def main():
    if 'id' not in session: session['id'] = 1 # Bypass para teste
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, nivel, saldo_real, heroi_img FROM players WHERE id = %s", (session['id'],))
    data = cur.fetchone()
    cur.close(); conn.close()
    return render_template_string(ARENA_HTML, user=data[0], lvl=data[1], saldo=data[2], hero_img=data[3])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
    
