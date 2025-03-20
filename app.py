from flask import Flask, render_template, request, redirect, url_for, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from contextlib import closing
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Chave secreta para sessões

# Configuração do banco de dados SQLite
DATABASE = 'database.db'

# Configuração da autenticação básica
auth = HTTPBasicAuth()

# Senha protegida (hash) - Carregada do arquivo .env
SENHA_ADMIN = os.getenv('SENHA_ADMIN')  # Carrega a senha do .env
USUARIOS = {
    "admin": generate_password_hash(SENHA_ADMIN)
}

# Função para verificar a senha
@auth.verify_password
def verificar_senha(usuario, senha):
    if usuario in USUARIOS and check_password_hash(USUARIOS.get(usuario), senha):
        return usuario

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Retorna resultados como dicionários
    return conn

# Cria a tabela de jogadores se não existir
def init_db():
    with closing(get_db_connection()) as conn:
        with app.open_resource('schema.sql', mode='r') as f:
            conn.executescript(f.read())
        conn.commit()

# Rota principal
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form['nome']
        nome_camiseta = request.form['nome_camiseta']
        numero = int(request.form['numero'])
        tamanho = request.form['tamanho']

        # Validações
        if numero < 1 or numero > 99:
            flash('Número inválido. Escolha um número entre 1 e 99.', 'error')
            return redirect(url_for('index'))

        if tamanho not in ['P', 'M', 'G', 'GG']:
            flash('Tamanho inválido. Escolha entre P, M, G ou GG.', 'error')
            return redirect(url_for('index'))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica se o número já foi escolhido
        cursor.execute('SELECT numero FROM jogadores WHERE numero = ?', (numero,))
        if cursor.fetchone():
            flash('Número já escolhido. Por favor, selecione outro.', 'error')
            conn.close()
            return redirect(url_for('index'))

        # Insere o novo jogador no banco de dados
        cursor.execute('''
            INSERT INTO jogadores (nome, nome_camiseta, numero, tamanho)
            VALUES (?, ?, ?, ?)
        ''', (nome, nome_camiseta, numero, tamanho))
        conn.commit()
        conn.close()

        flash('Inscrição realizada com sucesso!', 'success')
        return redirect(url_for('index'))

    # Carrega os números já utilizados
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT numero FROM jogadores')
    numeros_escolhidos = set(row['numero'] for row in cursor.fetchall())
    conn.close()

    # Gera a lista de números disponíveis
    numeros_disponiveis = [num for num in range(1, 100) if num not in numeros_escolhidos]
    return render_template('index.html', numeros_disponiveis=numeros_disponiveis)

# Rota protegida para listar jogadores
@app.route('/jogadores')
@auth.login_required
def listar_jogadores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jogadores ORDER BY numero')
    jogadores = cursor.fetchall()
    conn.close()
    return render_template('jogadores.html', jogadores=jogadores)

if __name__ == '__main__':
    init_db()  # Inicializa o banco de dados
    app.run(host='0.0.0.0', port=5000, debug=True)