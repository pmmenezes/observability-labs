# frontend/app.py

from flask import Flask, render_template_string
import requests
import os

app = Flask(__name__)

# URL do seu backend
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

# Template HTML simples para exibir os produtos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lista de Produtos - App Observability</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; text-align: center; }
        .product-list { list-style: none; padding: 0; }
        .product-item { background: #e9ecef; margin-bottom: 10px; padding: 15px; border-radius: 5px; }
        .product-item h2 { margin: 0 0 10px 0; color: #333; }
        .product-item p { margin: 5px 0; color: #555; }
        .product-item .price { font-weight: bold; color: #28a745; }
        .error { color: red; text-align: center; font-weight: bold; }
        .loading { text-align: center; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>��️ Nossos Produtos</h1>
        {% if products %}
            <ul class="product-list">
                {% for product in products %}
                    <li class="product-item">
                        <h2>{{ product.name }}</h2>
                        <p>{{ product.description }}</p>
                        <p class="price">R$ {{ "%.2f"|format(product.price) }}</p>
                    </li>
                {% endfor %}
            </ul>
        {% elif error %}
            <p class="error">{{ error }}</p>
        {% else %}
            <p class="loading">Carregando produtos...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Endpoint principal para exibir a lista de produtos."""
    products = []
    error = None
    try:
        # --- CENÁRIO DE ERRO NO FRONTEND (DESCOMENTE PARA ATIVAR) ---
        # Força um erro de divisão por zero na camada do frontend
        # resultado_erro_frontend = 10 / 0
        # print(f"Este print não será executado se o erro ocorrer: {resultado_erro_frontend}")
        # -----------------------------------------------------------
        # Faz a requisição para o endpoint de produtos do backend
        response = requests.get(f"{BACKEND_URL}/products")
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)
        products = response.json()
    except requests.exceptions.ConnectionError:
        error = f"Erro de conexão: Não foi possível conectar ao backend em {BACKEND_URL}. Certifique-se de que o backend esteja rodando."
        print(error)
    except requests.exceptions.RequestException as e:
        error = f"Erro ao obter produtos do backend: {e}"
        print(error)
    except Exception as e:
        error = f"Um erro inesperado ocorreu: {e}"
        print(error)

    return render_template_string(HTML_TEMPLATE, products=products, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
