from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import random 
import time   
import os
import logging


app = Flask(__name__)
CORS(app) # Habilite CORS para permitir requisições do frontend
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Função para obter conexão com o banco de dados
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'appdb'), # Substitua pelo nome do seu DB
        user=os.environ.get('DB_USER', 'appuser'),           # Substitua pelo seu usuário
        password=os.environ.get('DB_PASSWORD', 'apppassword') # Substitua pela sua senha
    )
    return conn

# Rota principal (pode ser ajustada)
@app.route('/')
def index():
    return jsonify({"message": "Bem-vindo ao Backend de Produtos!"})

# GET /products (Listar e Pesquisar Produtos)
@app.route('/products', methods=['GET'])
def get_products():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        search_query = request.args.get('search', '') # Captura o parâmetro 'search' da URL
       # time.sleep(2) # Atraso de 2 segundos

        if search_query:
            # Esta pesquisa por nome ou descrição (case-insensitive) com ILIKE '%term%'
            # será LENTA em um grande volume de dados se não houver um índice de trigram
            # ou se o '%` estiver no início, impedindo o uso de índices B-tree comuns.
            cur.execute("SELECT * FROM products WHERE name ILIKE %s OR description ILIKE %s",
                        (f"%{search_query}%", f"%{search_query}%"))
        else:
            # Retorna todos os produtos se não houver termo de pesquisa
            cur.execute("SELECT * FROM products")

        products = cur.fetchall()
        cur.close()
        return jsonify(products)
    except Exception as e:
        print(f"Erro ao recuperar produtos: {e}")
        return jsonify({"error": "Não foi possível recuperar os produtos."}), 500
    finally:
        if conn:
            conn.close()

# POST /products (Criar Novo Produto)
@app.route('/products', methods=['POST'])
def add_product():
    new_product = request.json # Pega os dados JSON do corpo da requisição
    name = new_product.get('name')
    description = new_product.get('description')
    price = new_product.get('price')

    # Validação básica
    if not name or not price:
        return jsonify({"error": "Nome e preço do produto são obrigatórios."}), 400
    try:
        price = float(price) # Garante que o preço é um número
    except ValueError:
        return jsonify({"error": "O preço deve ser um número válido."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, description, price) VALUES (%s, %s, %s) RETURNING id",
            (name, description, price)
        )
        product_id = cur.fetchone()[0] # Obtém o ID do produto inserido
        conn.commit() # Confirma a transação
        cur.close()
        return jsonify({"message": "Produto adicionado com sucesso!", "id": product_id}), 201 # 201 Created
    except Exception as e:
        if conn:
            conn.rollback() # Reverte a transação em caso de erro
        print(f"Erro ao adicionar produto: {e}")
        return jsonify({"error": "Não foi possível adicionar o produto."}), 500
    finally:
        if conn:
            conn.close()

# DELETE /products/<int:product_id> (Remover Produto)
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
        deleted_id = cur.fetchone() # Verifica se algum registro foi deletado
        conn.commit()
        cur.close()

        if deleted_id:
            return jsonify({"message": f"Produto com ID {product_id} deletado com sucesso!"}), 200
        else:
            return jsonify({"error": f"Produto com ID {product_id} não encontrado."}), 404 # 404 Not Found
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro ao deletar produto: {e}")
        return jsonify({"error": "Não foi possível deletar o produto."}), 500
    finally:
        if conn:
            conn.close()
# --- NOVA ROTA PARA SIMULAR CONSULTA LENTA ---
@app.route('/products/slow-search', methods=['GET'])
def slow_search_products():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # SIMULAÇÃO DE LENTIDÃO NO BANCO DE DADOS:
        # 1. Consulta com ORDER BY RANDOM() em uma tabela grande é muito ineficiente,
        # pois exige que o DB leia e ordene a tabela inteira.
        # 2. Consulta com ILIKE '%padrao%' sem índice apropriado força um "full table scan".
        # 3. Ou, uma consulta com JOINs complexos sem índices.

        # ESCOLHA UMA DAS OPÇÕES ABAIXO PARA SIMULAR A LENTIDÃO REAL NO DB:

        # Opção 1: ORDER BY RANDOM() - Clássico exemplo de consulta lenta
        print("SIMULANDO LENTIDÃO INTENCIONAL: ORDER BY RANDOM()")
        cur.execute("SELECT id, name, description, price FROM products ORDER BY RANDOM() LIMIT 10;")

        # Opção 2: Pesquisa com ILIKE em colunas não indexadas (se o termo for 'fascinante' ou 'qualidade', que populamos)
        # Descomente esta linha e comente a Opção 1 para testar
        # search_term = "fascinante"
        # print(f"SIMULANDO LENTIDÃO INTENCIONAL: ILIKE '%{search_term}%' em milhões de registros")
        # cur.execute("SELECT * FROM products WHERE description ILIKE %s;", (f"%{search_term}%",))

        # Opção 3: Consulta com JOIN complexo (requer mais tabelas, não aplicável diretamente aqui, mas um conceito)
        # Ex: SELECT p.* FROM products p JOIN another_large_table alt ON p.id = alt.product_id WHERE alt.some_col = 'value';    
    
    
        # Simula uma consulta lenta adicionando um atraso no codigo
        # Este atraso será detectado pelo New Relic como parte do tempo de banco de dados
        # print("SIMULANDO LENTIDÃO INTENCIONAL na consulta de produtos lentos...")
        # time.sleep(1.0) # Atraso de 1 segundo (1000 milissegundos)

        # Executa uma consulta simples para buscar todos os produtos
        cur.execute("SELECT * FROM products")
        
        products = cur.fetchall()
        cur.close()
        return jsonify(products)
    except Exception as e:
        print(f"Erro ao recuperar produtos lentos: {e}")
        return jsonify({"error": "Não foi possível recuperar os produtos lentos."}), 500
    finally:
        if conn:
            conn.close()
# --- FIM DA NOVA ROTA ---

# Rota para teste de erro (mantida para observability)
@app.route('/error-test')
def error_test():
    1/0 # Isso irá causar um ZeroDivisionError
    return "Esta linha não será alcançada"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
