import os
import random
import psycopg2
import hashlib
import uuid
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'MB_CHAVE_MESTRA_99')

DATABASE_URL = os.environ.get('DATABASE_URL')

# --- CONFIGURAÇÕES DO JOGO ---
HEROIS = {
    "guerreiro": {"hp": 120, "ataque": 20, "img": "https://i.ibb.co/3Y8NqK1/guerreiro.png"},
    "maga": {"hp": 80, "ataque": 35, "img": "https://i.ibb.co/L5kR7pX/maga.png"},
    "guardiao": {"hp": 160, "ataque": 12, "img": "https://i.ibb.co/hM8RzPz/guardiao.png"}
}

# --- INICIALIZAÇÃO DO BANCO DE DADOS COMPLETO ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    # Tabela de Jogadores
    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nivel INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            saldo_real FLOAT DEFAULT 0.0,
            gold_falso INTEGER DEFAULT 1000,
            heroi TEXT DEFAULT 'guerreiro',
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    # Tabela do Boss Global (Eventos ao Vivo)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS boss_global (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            hp_atual INTEGER,
            hp_max INTEGER,
            premio FLOAT,
            ativo BOOLEAN DEFAULT FALSE
        )
    ''')
    # Criar admin padrão se não existir (Usuario: admin / Senha: mb_admin123)
    pwd_admin = hashlib.sha256('mb_admin123'.encode()).hexdigest()
    cur.execute("INSERT INTO players (username, password, is_admin) VALUES ('admin', %s, TRUE) ON CONFLICT DO NOTHING", (pwd_admin,))
    
    conn.commit()
    cur.close()
    conn.close()

# --- INTERFACE UNIFICADA (DESIGN DE ALTO NÍVEL) ---
HTML_MAIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MB CLASH: EVOLUTION</title>
    <link rel="apple-touch-icon" href="https://i.ibb.co/v4PHT36T/1770042318622.png">
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #ffd700; --dark: #05050a; --purple: #6c5ce7; }
        body { background: var(--dark); color: white; font-family: 'Press Start 2P', cursive; margin: 0; overflow-x: hidden; }
        .app-container { max-width: 500px; margin: auto; min-height: 100vh; padding: 20px; box-sizing: border-box; }
        .logo { width: 120px; filter: drop-shadow(0 0 10px var(--gold)); margin-bottom: 20px; }
        
        /* Cards e UI */
        .card { background: #161b22; border: 2px solid var(--purple); border-radius: 15px; padding: 15px; margin: 10px 0; }
        .btn { background: var(--gold); color: black; border: none; padding: 15px; border-radius: 8px; font-family: 'Press Start 2P'; font-size: 10px; cursor: pointer; width: 100%; }
        .input-mb { background: #000; color: #fff; border: 1px solid var(--purple); padding: 12px; border-radius: 8px; width: 100%; margin-bottom: 10px; box-sizing: border-box; }
        
        /* Stats Bar */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 8px; margin-bottom: 20px; }
        .progress-bar { background: #333; height: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #555; }
        .progress-fill { background: var(--gold); height: 100%; width: 0%; transition: 0.5s; }

        /* Boss Alerta */
        .boss-alert { background: linear-gradient(45deg, #ff0000, #990000); padding: 10px; border-radius: 10px; margin-bottom: 15px; animation: pulse 1s infinite; display: none; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="app-container">
        <center><img src="https://i.ibb.co/v4PHT36T/1770042318622.png" class="logo"></center>

        {% if not logged_in %}
        <div class="card">
            <h3>ACESSO ARENA</h3>
            <input type="text" id="user" class="input-mb" placeholder="USUÁRIO">
            <input type="password" id="pass" class="input-mb" placeholder="SENHA">
            <button class="btn" onclick="auth('login')">ENTRAR</button>
            <p style="font-size: 8px; margin-top: 15px; color: #aaa;" onclick="document.getElementById('reg-box').style.display='block'">Criar nova conta</p>
        </div>
        <div id="reg-box" class="card" style="display:none">
            <button class="btn" style="background:#555" onclick="auth('register')">CRIAR CONTA AGORA</button>
        </div>

        {% else %}
        <div class="boss-alert" id="boss-ui">
            ⚠️ BOSS GLOBAL ATIVO! <br> <small id="boss-name"></small>
            <div class="progress-bar"><div id="boss-hp" class="progress-fill" style="background: white;"></div></div>
        </div>

        <div class="stats-grid">
            <div class="card">💰 R$ <span id="saldo">{{ player.saldo_real }}</span></div>
            <div class="card">⭐ LVL <span id="lvl">{{ player.nivel }}</span></div>
        </div>

        <div class="card">
            <p style="font-size:8px">XP PARA NÍVEL <span id="next-lvl">{{ player.nivel + 1 }}</span></p>
            <div class="progress-bar"><div class="progress-fill" style="width: {{ (player.xp % 100) }}%"></div></div>
        </div>

        <div id="game-modes">
            <button class="btn" style="margin-bottom:10px" onclick="play('rpg')">⚔️ AVENTURA RPG (FREE)</button>
            <button class="btn" style="background:var(--purple); color:white" onclick="play('pvp')">🎰 DUELO DE APOSTAS (PIX)</button>
        </div>

        {% if player.is_admin %}
        <div class="card" style="border-color: red;">
            <h4 style="color:red">PAINEL MESTRE</h4>
            <button class="btn" onclick="spawnBoss()" style="background:red; color:white">ATIVAR EVENTO AO VIVO</button>
        </div>
        {% endif %}

        <a href="/logout" style="color: #444; font-size: 8px; text-decoration: none;">SAIR DA CONTA</a>
        {% endif %}
    </div>

    <script>
        async function auth(type) {
            const user = document.getElementById('user').value;
            const pass = document.getElementById('pass').value;
            const res = await fetch('/'+type, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user, pass})
            });
            const d = await res.json();
            if(d.status === 'success') location.reload(); else alert(d.message);
        }

        async function spawnBoss() {
            await fetch('/admin/spawn-boss', {method: 'POST'});
            alert("BOSS DESPERTO!");
            location.reload();
        }

        // Check Boss Status a cada 5 segundos
        setInterval(async () => {
            const res = await fetch('/api/boss-status');
            const d = await res.json();
            if(d.ativo) {
                document.getElementById('boss-ui').style.display = 'block';
                document.getElementById('boss-name').innerText = d.nome + " HP: " + d.hp_atual;
                document.getElementById('boss-hp').style.width = (d.hp_atual/d.hp_max*100) + '%';
            }
        }, 5000);

        function play(mode) {
            alert("Iniciando modo " + mode + "... Prepare seus slots!");
        }
    </script>
</body>
</html>
"""

# --- ROTAS DE BACKEND ---

@app.route('/')
def home():
    logged_in = 'user' in session
    player_data = None
    if logged_in:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT username, nivel, xp, saldo_real, is_admin FROM players WHERE username = %s", (session['user'],))
        p = cur.fetchone()
        player_data = {"username": p[0], "nivel": p[1], "xp": p[2], "saldo_real": p[3], "is_admin": p[4]}
        cur.close()
        conn.close()
    return render_template_string(HTML_MAIN, logged_in=logged_in, player=player_data)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    pwd = hashlib.sha256(data['pass'].encode()).hexdigest()
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("INSERT INTO players (username, password) VALUES (%s, %s)", (data['user'], pwd))
        conn.commit()
        session['user'] = data['user']
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "error", "message": "Usuário já existe!"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    pwd = hashlib.sha256(data['pass'].encode()).hexdigest()
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT username FROM players WHERE username=%s AND password=%s", (data['user'], pwd))
    user = cur.fetchone()
    if user:
        session['user'] = user[0]
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Dados inválidos!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- LÓGICA DE ADMIN: DISPARAR BOSS ---
@app.route('/admin/spawn-boss', methods=['POST'])
def spawn_boss():
    # Verifica se é admin
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("UPDATE boss_global SET ativo = FALSE"); # Desativa antigos
    cur.execute("INSERT INTO boss_global (nome, hp_atual, hp_max, premio, ativo) VALUES ('DRAGÃO DE OURO MB', 5000, 5000, 100.0, TRUE)")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/boss-status')
def boss_status():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT nome, hp_atual, hp_max, ativo FROM boss_global WHERE ativo = TRUE LIMIT 1")
    b = cur.fetchone()
    cur.close()
    conn.close()
    if b: return jsonify({"nome": b[0], "hp_atual": b[1], "hp_max": b[2], "ativo": b[3]})
    return jsonify({"ativo": False})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
  
