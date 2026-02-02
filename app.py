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
        <title>MB CLASH - LOGIN</title>
        <style>
            body { background: #05050a; color: white; font-family: sans-serif; text-align: center; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
            .bg-herois { position: fixed; bottom: 0; width: 100%; display: flex; justify-content: space-around; z-index: -1; opacity: 0.5; }
            .heroi { width: 30%; max-width: 200px; animation: breathe 4s infinite alternate; }
            @keyframes breathe { from { transform: translateY(0); } to { transform: translateY(-20px); } }
            .login-box { background: rgba(0,0,0,0.85); padding: 30px; border: 2px solid #ffd700; border-radius: 20px; width: 90%; max-width: 380px; box-shadow: 0 0 20px rgba(255,215,0,0.2); }
            input { width: 100%; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #000; color: white; box-sizing: border-box; }
            button { width: 100%; padding: 15px; background: #ffd700; border: none; font-weight: bold; cursor: pointer; border-radius: 8px; font-size: 16px; margin-top: 10px; }
            .btn-suporte { display: block; margin-top: 20px; color: #3498db; text-decoration: none; font-size: 12px; font-weight: bold; }
            #msg { color: #ff4757; font-size: 13px; margin-top: 15px; min-height: 20px; }
        </style>
    </head>
    <body>
        <div class="bg-herois">
            <img src="https://img.freepik.com/fotos-premium/personagem-de-fantasia-de-mago-misterioso-com-cajado-magico-ia-generativa_201606-6130.jpg" class="heroi">
            <img src="https://img.freepik.com/fotos-premium/um-cavaleiro-em-armadura-dourada-e-preta-com-um-leao-no-peito_902639-25123.jpg" class="heroi">
            <img src="https://img.freepik.com/fotos-premium/guerreiro-de-armadura-pesada-em-estilo-rpg_941600-581.jpg" class="heroi">
        </div>

        <div class="login-box">
            <h1 style="color:#ffd700; margin-bottom:20px;">MB CLASH</h1>
            <input type="text" id="user" placeholder="NOME DE USUÁRIO">
            <input type="password" id="pass" placeholder="SENHA SECRETA">
            <button id="btn-entrar" onclick="logar()">ENTRAR NA ARENA</button>
            <div id="msg"></div>
            
            <a href="mailto:mbinformatica508@gmail.com?subject=Suporte%20MB%20Clash&body=Olá,%20estou%20com%20dificuldades%20para%20acessar%20o%20jogo." class="btn-suporte">
                📧 SUPORTE POR E-MAIL
            </a>
        </div>

        <script>
            async function logar() {
                const user = document.getElementById('user').value;
                const pass = document.getElementById('pass').value;
                const msg = document.getElementById('msg');
                const btn = document.getElementById('btn-entrar');
                
                if(!user || !pass) { msg.innerText = "Preencha todos os campos!"; return; }
                
                btn.innerText = "CONECTANDO AO BANCO...";
                btn.disabled = true;
                msg.innerText = "";
                
                try {
                    const res = await fetch('/login_action', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user, pass})
                    });
                    const d = await res.json();
                    
                    if(d.status === 'success') {
                        msg.style.color = "#2ed573";
                        msg.innerText = "SUCESSO! CARREGANDO JOGO...";
                        setTimeout(() => { window.location.href = '/'; }, 1000);
                    } else {
                        msg.innerText = "❌ " + d.message;
                        btn.innerText = "ENTRAR NA ARENA";
                        btn.disabled = false;
                    }
                } catch (e) {
                    msg.innerText = "⚠️ ERRO DE REDE: O servidor não respondeu.";
                    btn.innerText = "TENTAR NOVAMENTE";
                    btn.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """

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
    
