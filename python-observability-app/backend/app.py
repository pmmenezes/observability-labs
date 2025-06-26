# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app) # Habilita CORS para permitir requisições do frontend

# Configurações do banco de dados (pode ser carregado de variáveis de ambiente)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'appdb')
DB_USER = os.getenv('DB_USER', 'appuser')
DB_PASS = os.getenv('DB_PASS', 'apppassword')

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados PostgreSQL."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise # Levanta a exceção para que a aplicação possa lidar com ela

@app.route('/products', methods=['GET'])
def get_products():
    """Endpoint para listar todos os produtos."""
    conn = None
    try:
        # --- CENÁRIO DE ERRO NO BACKEND (DESCOMENTE PARA ATIVAR) ---
        # Simula um erro de lógica de negócios (KeyError)
        # dados_errados = {"nome": "Produto X"}
        # print(dados_errados["preco"]) # Isso irá gerar um KeyError
        # -----------------------------------------------------------
        conn = get_db_connection()
        cur = conn.cursor()
        # --- CENÁRIO DE ERRO NO BANCO DE DADOS (DESCOMENTE UMA DAS LINHAS PARA ATIVAR) ---
        # 1. Tentativa de selecionar uma coluna que não existe na tabela 'products'
        # cur.execute('SELECT id, name, non_existent_column, price FROM products;')        
        # 2. Tentativa de selecionar de uma tabela que não existe
        # cur.execute('SELECT id, name FROM non_existent_table;')
        # -------------------------------------------------------------------------------
        cur.execute('SELECT id, name, description, price FROM products;')
        products = cur.fetchall()
        cur.close()
        conn.close()

        # Formata os resultados como uma lista de dicionários
        products_list = []
        for product in products:
            products_list.append({
                'id': product[0],
                'name': product[1],
                'description': product[2],# Esta linha pode causar um IndexError se a query falhar antes
                'price': float(product[3]) # Converte Decimal para float
            })
        
        return jsonify(products_list), 200
    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
        # Retorna um erro 500 em caso de falha interna
        return jsonify({"error": "Erro interno do servidor ao buscar produtos."}), 500
    finally:
        if conn:
            conn.close()

@app.route('/', methods=['GET'])
def status_check():
    """Endpoint simples para verificar se o backend está funcionando."""
    return jsonify({"status": "Backend is running!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
