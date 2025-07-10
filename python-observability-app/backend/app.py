from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import random 
import time   
import os
import logging
from psycopg2 import errors as pg_errors 


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

# --- NOVA ROTA PARA SIMULAR DIVERSOS TIPOS DE ERROS DE DB ---
@app.route('/products/db-error-test', methods=['GET'])
def db_error_test():
    error_type = request.args.get('type', 'none') # Captura o tipo de erro a simular
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor() # Não precisamos de RealDictCursor para estes testes simples

        if error_type == 'no_table':
            print("Simulando: Tabela inexistente...")
            cur.execute("SELECT * FROM non_existent_table;")
            
        elif error_type == 'unique_violation':
            print("Simulando: Violação de UNIQUE constraint...")
            # Tenta inserir um produto com o mesmo nome de um já existente
            # Assumindo que 'name' deveria ser UNIQUE (vamos forçar isso no SQL de init)
            # ou que você tentará inserir o primeiro produto novamente.
            cur.execute("INSERT INTO products (name, description, price) VALUES (%s, %s, %s);",
                        ('Monitor UltraWide', 'Tentativa de duplicata', 100.00))
            conn.commit() # Commit para que o erro ocorra (ou seja revertido)

        elif error_type == 'no_column':
            print("Simulando: Coluna inexistente...")
            cur.execute("SELECT non_existent_column FROM products;")
            
        elif error_type == 'syntax_error':
            print("Simulando: Erro de sintaxe SQL...")
            cur.execute("SELECT * FROM products WHER id = 1;") # 'WHER' é erro

        elif error_type == 'not_null_violation':
            print("Simulando: Violação de NOT NULL constraint...")
            cur.execute("INSERT INTO products (name, price) VALUES (NULL, 50.00);") # 'name' é NOT NULL
            conn.commit() # Commit para que o erro ocorra

        elif error_type == 'data_truncation':
            print("Simulando: Truncamento de dados (string muito longa)...")
            long_name = "A" * 300 # products.name é VARCHAR(255)
            cur.execute("INSERT INTO products (name, description, price) VALUES (%s, %s, %s);",
                        (long_name, 'Desc', 10.00))
            conn.commit()

        # Adicione mais tipos de erro conforme necessário

        else:
            return jsonify({"message": "Nenhum erro de DB simulado. Use ?type=no_table, unique_violation, no_column, syntax_error, not_null_violation, data_truncation."}), 200

        # Se a execução chegar aqui, significa que a query (que deveria falhar) foi executada.
        # Na maioria dos casos, a exceção será levantada antes.
        cur.close()
        return jsonify({"message": f"Erro de DB '{error_type}' deveria ter ocorrido. Verifique logs."}), 500

    except (pg_errors.UndefinedTable, # Erro para tabela inexistente
            pg_errors.UniqueViolation, # Erro para violação de UNIQUE
            pg_errors.UndefinedColumn, # Erro para coluna inexistente
            pg_errors.SyntaxError, # Erro de sintaxe SQL
            pg_errors.NotNullViolation, # Erro para NOT NULL
            pg_errors.StringDataRightTruncation, # Erro para truncamento de dados
            psycopg2.Error # Captura qualquer outro erro de psycopg2
            ) as e:
        if conn:
            conn.rollback() # Reverte a transação em caso de erro
        error_message = str(e).strip().replace('\n', ' ') # Limpa a mensagem para JSON
        print(f"ERRO DE DB SIMULADO ({error_type}): {error_message}")
        return jsonify({"error": f"Erro de DB simulado: {error_type}. Detalhes: {error_message}"}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro inesperado no db-error-test: {e}")
        return jsonify({"error": f"Erro inesperado: {str(e)}."}), 500
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
