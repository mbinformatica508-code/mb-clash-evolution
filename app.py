import os
import psycopg2
import hashlib
from flask import Flask, render_template_string, jsonify, request, session, redirect

app = Flask(__name__)
app.secret_key = 'MB_CLASH_99_SUPER_SECRET'

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    # Conexão segura obrigatória para o Render
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        # Garante que o admin exista (Usuario: admin / Senha: mb_admin123)
        pwd_admin = hashlib.sha256('mb_admin123'.encode()).hexdigest()
        cur.execute("INSERT INTO players (username, password, is_admin) VALUES ('admin', %s, TRUE) ON CONFLICT DO NOTHING", (pwd_admin,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na inicialização do banco: {e}")

@app.route('/')
def home():
    if 'user' in session:
        return f"""
        <html>
            <body style="background:#05050a; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
                <h1 style="color:#ffd700">MB CLASH: LOGADO</h1>
                <p>Bem-vindo, {session['user'].upper()}!</p>
                { '<div style="border:2px solid red; padding:20px; margin:20px; border-radius:15px;"><h2 style="color:red">PAINEL MESTRE</h2><button style="background:red; color:white; padding:15px; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">LANÇAR BOSS GLOBAL</button></div>' if session.get('is_admin') else '' }
                <br>
                <a href="/logout" style="color:#555; text-decoration:none;">[ SAIR DA CONTA ]</a>
            </body>
        </html>
        """
    
    return """
    <!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MB CLASH - Arena Evolution</title>
    <style>
        body {
            background: radial-gradient(circle, #1a1a2e 0%, #0f0f1a 100%);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
        }

        .battle-arena {
            background: url('https://your-image-link.com/arena.jpg') center/cover;
            border: 4px solid #4ecca3;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            height: 400px;
            margin: 20px auto;
            position: relative;
            box-shadow: 0 0 30px rgba(78, 204, 163, 0.3);
        }

        .player-bar {
            position: absolute;
            top: 20px;
            left: 20px;
            width: 250px;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px;
            border-radius: 8px;
            border-left: 5px solid #ff4b2b;
        }

        .hp-bar {
            background: #333;
            height: 15px;
            border-radius: 10px;
            overflow: hidden;
        }

        .hp-fill {
            background: linear-gradient(90deg, #ff416c, #ff4b2b);
            width: 80%; /* Dinâmico via Python */
            height: 100%;
        }

        .action-buttons {
            margin-top: 30px;
            display: flex;
            justify-content: center;
            gap: 15px;
        }

        .btn-pix {
            background: #32bcad;
            color: black;
            font-weight: bold;
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            transition: 0.3s;
            box-shadow: 0 5px 15px rgba(50, 188, 173, 0.4);
        }

        .btn-pix:hover {
            transform: scale(1.1);
            filter: brightness(1.2);
        }
    </style>
</head>
<body>
    <h1>⚔️ MB CLASH: EVOLUÇÃO ⚔️</h1>
    
    <div class="battle-arena">
        <div class="player-bar">
            <strong>Mateus Bispo</strong> <br>
            Nível 15 | Guerreiro Master
            <div class="hp-bar"><div class="hp-fill"></div></div>
        </div>
        </div>

    <div class="action-buttons">
        <button class="btn-pix">SOLTAR PODER (50 Gold)</button>
        <a href="/comprar-gold" class="btn-pix" style="background: #ffd700;">💰 RECARGA PIX (BÔNUS 20%)</a>
    </div>
</body>
</html>

@app.route('/login_action', methods=['POST'])
def login_action():
    data = request.json
    user_input = data.get('user')
    pass_input = data.get('pass')
    pwd_hashed = hashlib.sha256(pass_input.encode()).hexdigest()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, is_admin FROM players WHERE username=%s AND password=%s", (user_input, pwd_hashed))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user'] = user[0]
            session['is_admin'] = user[1]
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Usuário ou senha inválidos."})
    except Exception as e:
        # Aqui ele manda o erro real do banco para a sua tela do celular
        return jsonify({"status": "error", "message": f"Erro no Banco: {str(e)}"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
