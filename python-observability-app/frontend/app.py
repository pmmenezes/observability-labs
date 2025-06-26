# frontend/app.py

from flask import Flask, render_template_string, request # 'request' não é estritamente necessário para esta abordagem, mas mantenha para flexibilidade
import requests
import os

app = Flask(__name__)

# URL do seu backend
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

# Template HTML completo com JavaScript para interatividade
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerenciamento de Produtos - App Observability</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { color: #0056b3; text-align: center; }
        form { background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        form label { display: block; margin-bottom: 5px; font-weight: bold; }
        form input[type="text"], form input[type="number"], form textarea {
            width: calc(100% - 22px); padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; margin-bottom: 15px;
        }
        form button {
            background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;
        }
        form button.add { background: #28a745; }
        form button.search { background: #007bff; }
        form button.clear { background: #6c757d; margin-left: 10px;}
        .product-list { list-style: none; padding: 0; }
        .product-item {
            background: #fff; border: 1px solid #eee; padding: 15px; margin-bottom: 10px; border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;
        }
        .product-item h3 { margin: 0 0 5px 0; color: #0056b3; }
        .product-item p { margin: 0 0 5px 0; color: #666; }
        .product-item .price { font-weight: bold; color: #333; }
        .product-item button { background: #dc3545; color: white; padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .message { text-align: center; font-weight: bold; padding: 10px; margin-bottom: 10px; border-radius: 4px;}
        .error-message { color: red; background-color: #ffe0e0; border: 1px solid #ffb3b3; }
        .loading-message { color: #666; }
        .success-message { color: green; background-color: #e0ffe0; border: 1px solid #b3ffb3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Gerenciamento de Produtos</h1>

        <div id="messages"></div>

        <!-- Formulário para Adicionar Produto -->
        <h2>Adicionar Novo Produto</h2>
        <form id="addProductForm">
            <label for="addName">Nome:</label>
            <input type="text" id="addName" required><br>

            <label for="addDescription">Descrição:</label>
            <textarea id="addDescription"></textarea><br>

            <label for="addPrice">Preço:</label>
            <input type="number" id="addPrice" step="0.01" required><br>

            <button type="submit" class="add">Adicionar Produto</button>
        </form>

        <!-- Formulário para Pesquisar Produtos -->
        <h2>Pesquisar Produtos</h2>
        <form id="searchProductForm">
            <label for="searchTerm">Termo de Busca:</label>
            <input type="text" id="searchTerm" placeholder="Buscar por nome ou descrição"><br>
            <button type="submit" class="search">Buscar</button>
            <button type="button" id="clearSearchButton" class="clear">Limpar Busca</button>
        </form>

        <!-- Lista de Produtos -->
        <h2>Produtos Disponíveis</h2>
        <ul id="productList" class="product-list">
            <!-- Produtos serão carregados aqui pelo JavaScript -->
        </ul>
    </div>

    <script>
        const BACKEND_URL = '{{ BACKEND_URL }}'; // Flask injeta a URL do backend aqui
        const productList = document.getElementById('productList');
        const addProductForm = document.getElementById('addProductForm');
        const searchProductForm = document.getElementById('searchProductForm');
        const clearSearchButton = document.getElementById('clearSearchButton');
        const messagesDiv = document.getElementById('messages');

        // Função para exibir mensagens ao usuário
        function displayMessage(msg, type) {
            messagesDiv.innerHTML = `<p class="message ${type}-message">${msg}</p>`;
            setTimeout(() => { messagesDiv.innerHTML = ''; }, 5000); // Limpa a mensagem após 5 segundos
        }

        // Função para buscar e exibir os produtos
        async function fetchProducts(searchTerm = '') {
            displayMessage('Carregando produtos...', 'loading');
            try {
                const url = searchTerm ? `${BACKEND_URL}/products?search=${encodeURIComponent(searchTerm)}` : `${BACKEND_URL}/products`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Erro HTTP: ${response.status}`);
                }
                const products = await response.json();
                productList.innerHTML = ''; // Limpa a lista atual
                if (products.length === 0) {
                    productList.innerHTML = '<p class="loading-message">Nenhum produto encontrado.</p>';
                } else {
                    products.forEach(product => {
                        const li = document.createElement('li');
                        li.className = 'product-item';
                        li.innerHTML = `
                            <div>
                                <h3>${product.name}</h3>
                                <p>${product.description || ''}</p>
                                <p class="price">R$ ${parseFloat(product.price).toFixed(2)}</p>
                            </div>
                            <button data-id="${product.id}">Deletar</button>
                        `;
                        // Adiciona o evento de clique para o botão Deletar
                        li.querySelector('button').addEventListener('click', () => deleteProduct(product.id));
                        productList.appendChild(li);
                    });
                }
                messagesDiv.innerHTML = ''; // Limpa a mensagem de carregamento em caso de sucesso
            } catch (error) {
                console.error('Erro ao buscar produtos:', error);
                displayMessage(`Erro ao carregar produtos: ${error.message}`, 'error');
            }
        }

        // Função para adicionar um novo produto
        async function addProduct(event) {
            event.preventDefault(); // Previne o envio padrão do formulário (que recarregaria a página)
            const name = document.getElementById('addName').value;
            const description = document.getElementById('addDescription').value;
            const price = document.getElementById('addPrice').value;

            if (!name || !price) {
                displayMessage('Nome e preço são obrigatórios!', 'error');
                return;
            }

            try {
                const response = await fetch(`${BACKEND_URL}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description, price: parseFloat(price) })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || response.statusText);
                }

                displayMessage('Produto adicionado com sucesso!', 'success');
                addProductForm.reset(); // Limpa os campos do formulário
                fetchProducts(); // Recarrega a lista de produtos
            } catch (error) {
                console.error('Erro ao adicionar produto:', error);
                displayMessage(`Erro ao adicionar produto: ${error.message}`, 'error');
            }
        }

        // Função para deletar um produto
        async function deleteProduct(id) {
            if (!confirm(`Tem certeza que deseja deletar o produto com ID ${id}?`)) {
                return; // Usuário cancelou
            }
            try {
                const response = await fetch(`${BACKEND_URL}/products/${id}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || response.statusText);
                }

                displayMessage('Produto deletado com sucesso!', 'success');
                fetchProducts(); // Recarrega a lista de produtos
            } catch (error) {
                console.error('Erro ao deletar produto:', error);
                displayMessage(`Erro ao deletar produto: ${error.message}`, 'error');
            }
        }

        // Função para pesquisa (chamada pelo formulário de busca)
        function searchProducts(event) {
            event.preventDefault(); // Previne o envio padrão do formulário
            const searchTerm = document.getElementById('searchTerm').value;
            fetchProducts(searchTerm);
        }

        // Função para limpar a busca
        function clearSearch() {
            document.getElementById('searchTerm').value = '';
            fetchProducts(); // Recarrega todos os produtos
        }

        // Adiciona os event listeners aos formulários e botões
        addProductForm.addEventListener('submit', addProduct);
        searchProductForm.addEventListener('submit', searchProducts);
        clearSearchButton.addEventListener('click', clearSearch);

        // Carrega os produtos ao iniciar a página
        document.addEventListener('DOMContentLoaded', () => fetchProducts());
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Endpoint principal para exibir a interface de gerenciamento de produtos."""
    # O frontend agora renderiza o HTML e o JavaScript no lado do cliente
    # que fará as chamadas AJAX para o backend.
    # A variável BACKEND_URL é injetada no template para ser usada pelo JS.
    return render_template_string(HTML_TEMPLATE, BACKEND_URL=BACKEND_URL)

# Rota para teste de erro (mantida para observability)
@app.route('/error-test-frontend')
def error_test_frontend():
    # Este erro não será pego pelo New Relic APM Python Agent,
    # pois ocorre no lado do cliente (JavaScript) depois que o HTML é servido.
    # Para capturar erros de JavaScript, você precisaria de RUM (Real User Monitoring).
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Frontend Error Test</title></head>
        <body>
            <h1>Teste de Erro de Frontend (JavaScript)</h1>
            <script>
                // Força um erro JavaScript no lado do cliente
                throw new Error("Erro simulado no frontend (JavaScript)");
            </script>
        </body>
        </html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)