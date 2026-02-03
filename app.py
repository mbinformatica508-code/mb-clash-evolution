import os
import psycopg2
from flask import Flask, render_template_string, request, session, redirect, jsonify

app = Flask(__name__)
app.secret_key = "MB_CLASH_SUPER_SECRET_KEY" #

# Configurações de Ambiente (Koyeb/Neon)
DATABASE_URL = os.environ.get("DATABASE_URL") #
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN") #

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require") #

# Interface Visual Unificada (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>MB CLASH - Arena Master</title>
    <style>
        :root { --neon: #4ecca3; --danger: #ff4b2b; --gold: #ffd700; }
        body { margin: 0; background: #0f0f1a; color: white; font-family: sans-serif; overflow: hidden; }
        
        /* Cabeçalho e HUD */
        .hud { position: fixed; top: 0; width: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: space-around; padding: 10px; border-bottom: 2px solid var(--neon); z-index: 10; }
        
        /* Arena */
        #arena { width: 100vw; height: 60vh; background: url('https://imgur.com/vH6ZzV6.png') center/cover; position: relative; }
        #player { 
            width: 80px; height: 80px; 
            background: url('{{ hero_img }}') no-repeat center; 
            background-size: contain; position: absolute; bottom: 50px; left: 50px; 
            transition: transform 0.1s; 
        }

        /* Controles */
        .controls { height: 40vh; background: #1a1a2e; display: flex; justify-content: space-evenly; align-items: center; }
        .btn-action { padding: 20px 40px; border-radius: 50px; border: none; font-weight: bold; cursor: pointer; font-size: 1.2rem; }
        .attack { background: var(--danger); box-shadow: 0 0 15px var(--danger); }
        .jump { background: var(--neon); }
        .btn-pix { background: var(--gold); color: black; }
    </style>
</head>
<body>
    <div class="hud">
        <span>👤 {{ username }} (Nível {{ nivel }})</span>
        <span>💰 Saldo: R$ {{ "%.2f"|format(saldo) }}</span>
    </div>

    <div id="arena">
        <div id="player"></div>
    </div>

    <div class="controls">
        <div class="d-pad">
            <button class="btn-action" onmousedown="move('left')">◀</button>
            <button class="btn-action" onmousedown="move('right')">▶</button>
        </div>
        <div class="actions">
            <button class="btn-action attack" onclick="performAttack()">⚔️ ATACAR</button>
            <button class="btn-action jump" onclick="performJump()">🚀 PULAR</button>
            <button class="btn-action btn-pix" onclick="window.location.href='/loja'">🪙 RECARGA</button>
        </div>
    </div>

    <script>
        let posX = 50;
        const player = document.getElementById('player');

        function move(dir) {
            if(dir === 'right') posX += 20;
            if(dir === 'left') posX -= 20;
            player.style.left = posX + 'px';
        }

        function performJump() {
            player.style.transform = 'translateY(-100px)';
            setTimeout(() => player.style.transform = 'translateY(0)', 300);
        }

        function performAttack() {
            player.style.filter = 'brightness(2)';
            setTimeout(() => player.style.filter = 'brightness(1)', 100);
        }

        // Movimentação via Teclado
        document.addEventListener('keydown', (e) => {
            if(e.key === 'ArrowRight') move('right');
            if(e.key === 'ArrowLeft') move('left');
            if(e.key === ' ') performJump();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Busca dados reais do banco Neon
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, nivel, saldo_real, heroi_img FROM players WHERE id = %s", (session['user_id'],))
    user_data = cur.fetchone()
    cur.close()
    conn.close()

    return render_template_string(HTML_TEMPLATE, 
                                 username=user_data[0], 
                                 nivel=user_data[1], 
                                 saldo=user_data[2],
                                 hero_img=user_data[3])

@app.route('/login')
def login_simulado():
    # Simulação de login para teste rápido
    session['user_id'] = 1
    return redirect('/')

if __name__ == "__main__":
    # Comando de execução obrigatório para Koyeb
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
    
