import os
import random
import psycopg2
import hashlib
import uuid
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'MB_CHAVE_MESTRA_99') # Mantenha a chave segura e única!

DATABASE_URL = os.environ.get('DATABASE_URL')

# --- CONFIGURAÇÕES DOS HERÓIS (PARA EXIBIÇÃO NO LOGIN) ---
HEROIS_LOGIN = [
    {"nome": "FEITICEIRA", "img": "https://i.ibb.co/CByy69t/feiticeira.png", "hp": 80}, # Primeiro herói
    {"nome": "PALADINO", "img": "https://i.ibb.co/zX10wP5/paladino.png", "hp": 120}, # Herói do meio
    {"nome": "COLOSSO", "img": "https://i.ibb.co/hK714Y4/colosso.png", "hp": 150}  # Último herói
]
# Os links para as imagens foram atualizados conforme sua imagem gerada.

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
            heroi TEXT DEFAULT 'guerreiro', -- Herói inicial, pode ser selecionado no jogo
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

# Função para encriptar senhas
def encrypt_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# --- INTERFACE UNIFICADA COM LOGIN ESTILIZADO E ANIMAÇÕES ---
HTML_MAIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MB CLASH: A ASCENSÃO</title>
    <link rel="apple-touch-icon" href="https://i.ibb.co/v4PHT36T/1770042318622.png">
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        :root { 
            --gold: #ffd700; 
            --dark: #05050a; 
            --purple: #6c5ce7; 
            --red-boss: #cc0000;
        }
        body { 
            background: var(--dark); 
            color: white; 
            font-family: 'Press Start 2P', cursive; 
            margin: 0; 
            overflow: hidden; /* Evita scroll na animação */
            text-align: center;
        }
        .app-container { 
            max-width: 500px; 
            margin: auto; 
            min-height: 100vh; 
            padding: 20px; 
            box-sizing: border-box; 
            position: relative;
            z-index: 2; /* Acima do background */
        }
        .logo { 
            width: 120px; 
            filter: drop-shadow(0 0 10px var(--gold)); 
            margin-bottom: 20px; 
            margin-top: 10px;
        }
        
        /* Background animado dos heróis */
        .hero-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: space-around;
            align-items: flex-end; /* Heróis na base */
            overflow: hidden;
            z-index: 1; /* Atrás do conteúdo */
            background-image: url('https://i.ibb.co/JnHjD4k/background-city-fantasy.png'); /* Fundo de cidade/castelo */
            background-size: cover;
            background-position: center bottom;
        }
        .hero-bg-item {
            position: absolute;
            bottom: 0;
            width: 30%; /* Para os 3 heróis */
            max-width: 200px; /* Limite de tamanho */
            animation: breathe 5s infinite alternate; /* Animação de "respiração" */
        }
        .hero-bg-item:nth-child(1) { left: 5%; animation-delay: 0s; } /* Feiticeira */
        .hero-bg-item:nth-child(2) { left: 35%; animation-delay: 0.5s; } /* Paladino */
        .hero-bg-item:nth-child(3) { left: 65%; animation-delay: 1s; } /* Colosso */

        @keyframes breathe {
            0% { transform: translateY(0px) scale(1); filter: brightness(0.8); }
            50% { transform: translateY(-5px) scale(1.02); filter: brightness(1.2); }
            100% { transform: translateY(0px) scale(1); filter: brightness(0.8); }
        }

        /* Cards e UI */
        .card { 
            background: rgba(22, 27, 34, 0.9); /* Fundo semi-transparente */
            border: 2px solid var(--purple); 
            border-radius: 15px; 
            padding: 15px; 
            margin: 10px 0; 
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.7);
        }
        .btn { 
            background: var(--gold); 
            color: black; 
            border: none; 
            padding: 15px; 
            border-radius: 8px; 
            font-family: 'Press Start 2P'; 
            font-size: 10px; 
            cursor: pointer; 
            width: 100%; 
            margin-top: 10px;
            transition: background 0.3s, transform 0.3s;
        }
        .btn:hover {
            background: #e0b800;
            transform: translateY(-2px);
        }
        .input-mb { 
            background: #000; 
            color: #fff; 
            border: 1px solid var(--purple); 
            padding: 12px; 
            border-radius: 8px; 
            width: calc(100% - 24px); /* Ajuste para padding */
            margin-bottom: 10px; 
            box-sizing: border-box; 
            font-family: 'Press Start 2P', cursive;
            font-size: 10px;
        }
        
        /* Stats Bar */
        .stats-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 10px; 
            font-size: 8px; 
            margin-bottom: 20px; 
        }
        .progress-bar { 
            background: #333; 
            height: 10px; 
            border-radius: 5px; 
            margin-top: 5px; 
            border: 1px solid #555; 
            overflow: hidden;
        }
        .progress-fill { 
            background: var(--gold); 
            height: 100%; 
            width: 0%; 
            transition: 0.5s; 
        }

        /* Boss Alerta */
        .boss-alert { 
            background: linear-gradient(45deg, #ff0000, #990000); 
            padding: 10px; 
            border-radius: 10px; 
            margin-bottom: 15px; 
            animation: pulse 1s infinite; 
            display: none; 
        }
        @keyframes pulse { 
            0% { opacity: 1; } 
            50% { opacity: 0.7; } 
            100% { opacity: 1; } 
        }

        /* Botão de Suporte */
        .support-btn {
            background: #3498db;
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 9px;
            margin-top: 20px;
            display: inline-block;
            text-decoration: none;
        }

        /* Mídia para celulares pequenos */
        @media (max-width: 400px) {
            .hero-bg-item { width: 40%; max-width: 150px; }
            .hero-bg-item:nth-child(1) { left: -5%; }
            .hero-bg-item:nth-child(2) { left: 30%; }
            .hero-bg-item:nth-child(3) { left: 65%; }
        }
    </style>
</head>
<body>
    <audio id="bg-music" loop autoplay>
        <source src="https://www.chosic.com/wp-content/uploads/2021/04/Magic-Knight-RPG-Music.mp3" type="audio/mpeg">
        Seu navegador não suporta áudio.
    </audio>

    <div class="hero-background">
        <img src="{{ HEROIS_LOGIN[0].img }}" class="hero-bg-item">
        <img src="{{ HEROIS_LOGIN[1].img }}" class="hero-bg-item">
        <img src="{{ HEROIS_LOGIN[2].img }}" class="hero-bg-item">
    </div>

    <div class="app-container">
        <center><img src="https://i.ibb.co/v4PHT36T/1770042318622.png" class="logo"></center>

        {% if not logged_in %}
        <div class="card">
            <h3>ACESSO ARENA</h3>
            <input type="text" id="user" class="input-mb" placeholder="USUÁRIO">
            <input type="password" id="pass" class="input-mb" placeholder="SENHA">
            <button class="btn" onclick="auth('login')">ENTRAR</button>
            <p style="font-size: 8px; margin-top: 15px; color: #aaa; cursor: pointer;" onclick="document.getElementById('reg-box').style.display='block'; document.getElementById('login-btn-card').style.display='none'">Criar nova conta</p>
        </div>
        <div id="reg-box" class="card" style="display:none">
            <button class="btn" style="background:#555" onclick="auth('register')">CRIAR CONTA AGORA</button>
            <p style="font-size: 8px; margin-top: 15px; color: #aaa; cursor: pointer;" onclick="document.getElementById('reg-box').style.display='none'; document.getElementById('login-btn-card').style.display='block'">Já tenho uma conta</p>
        </div>
        
        <a href="https://wa.me/SEU_NUMERO_DE_WHATSAPP?text=Olá,%20preciso%20de%20suporte%20no%20MB%20Clash!" target="_blank" class="support-btn">SUPORTE VIA WHATSAPP</a>

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
        document.addEventListener('DOMContentLoaded', (event) => {
            // Toca a música automaticamente (pode ser bloqueado por alguns navegadores sem interação do usuário)
            const bgMusic = document.getElementById('bg-music');
            if (bgMusic) {
                bgMusic.volume = 0.3; // Volume baixo para não atrapalhar
                bgMusic.play().catch(e => console.log("Música bloqueada pelo navegador, aguardando interação."));
            }
        });

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
            // Este endpoint precisaria de mais lógica para criar o boss com nome, HP, prêmio, etc.
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
            } else {
                document.getElementById('boss-ui').style.display = 'none';
            }
        }, 5000);

        function play(mode) {
            alert("Iniciando modo " + mode + "... Prepare seus slots!");
            // Aqui você adicionaria a lógica para redirecionar para a página do jogo real
        }
    </script>
</body>
</html>
"""

# --- ROTAS DE BACKEND (Não alteradas, mantidas do código anterior) ---

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
    return render_template_string(HTML_MAIN, logged_in=logged_in, player=player_data, HEROIS_LOGIN=HEROIS_LOGIN)

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
    except Exception as e:
        return jsonify({"status": "error", "message": "Usuário já existe ou erro no cadastro!"})

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
    # Verifica se é admin (adicionar verificação de session['user'] aqui para segurança real)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("UPDATE boss_global SET ativo = FALSE"); # Desativa antigos
    # Aqui o admin poderia definir nome, HP e prêmio do boss via um formulário
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
