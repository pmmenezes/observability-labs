from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app) # Habilite CORS para permitir requisições do frontend

# Função para obter conexão com o banco de dados
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'products_db'), # Substitua pelo nome do seu DB
        user=os.environ.get('DB_USER', 'user'),           # Substitua pelo seu usuário
        password=os.environ.get('DB_PASSWORD', 'password') # Substitua pela sua senha
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

        if search_query:
            # Pesquisa por nome ou descrição (case-insensitive)
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

# Rota para teste de erro (mantida para observability)
@app.route('/error-test')
def error_test():
    1/0 # Isso irá causar um ZeroDivisionError
    return "Esta linha não será alcançada"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)