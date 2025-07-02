# app.py (Backend com Flask e PostgreSQL)

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os # Necessário para acessar variáveis de ambiente do Render

# 1. Cria a instância do Flask AQUI, no nível superior do arquivo.
# Isso garante que o Gunicorn possa encontrá-la.
app = Flask(__name__)

# 2. Configuração do Banco de Dados PostgreSQL
# A URL do banco de dados virá do Render via variável de ambiente DATABASE_URL
# O .get('DATABASE_URL') tenta pegar a variável do ambiente, se não encontrar,
# usa 'sqlite:///app.db' para testes locais, mas no Render sempre virá da variável.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Boa prática para evitar warnings

db = SQLAlchemy(app) # Inicializa o SQLAlchemy com a instância 'app'
CORS(app) # Habilita CORS para permitir que seu frontend KivyMD se conecte

# --- 3. Modelo de Usuário (Representa a tabela 'users' no banco de dados) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

# --- 4. Rotas da API ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Usuário e senha são obrigatórios"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Nome de usuário já existe"}), 409

    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except Exception as e:
        db.session.rollback() # Desfaz a operação em caso de erro
        return jsonify({"message": f"Erro no servidor ao registrar: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Usuário e senha são obrigatórios"}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # Em uma aplicação real, você geraria um JWT (JSON Web Token) aqui para autenticação
        # Por simplicidade, vamos apenas retornar uma mensagem de sucesso e um placeholder de token.
        return jsonify({"message": "Login bem-sucedido!", "token": "seu_token_jwt_aqui_ou_futuro"}), 200
    else:
        return jsonify({"message": "Nome de usuário ou senha inválidos"}), 401

# Rota raiz para verificar se a API está online
@app.route('/')
def home():
    return jsonify({"message": "API de Autenticação para ASD online!"})

# --- 5. Script de Inicialização Local ---
# Este bloco SÓ é executado quando você roda o arquivo diretamente (python app.py)
# NÃO é executado pelo Gunicorn no Render, que usa 'app = Flask(__name__)' diretamente.
if __name__ == '__main__':
    with app.app_context(): # Garante que o contexto da aplicação esteja ativo para operações de banco de dados
        db.create_all() # Cria as tabelas no banco de dados se não existirem
    app.run(debug=True, port=5000) # Inicia o servidor Flask localmente
