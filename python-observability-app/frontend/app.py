# frontend/app.py

from flask import Flask, render_template_string, request
import requests
import os
import logging
import socket # Importar o módulo socket
# Função para obter o IP local da máquina
def get_local_ip():
    """
    Tenta obter o endereço IP local da máquina.
    Ele se conecta a um endereço externo (como um servidor DNS conhecido)
    para determinar a interface de rede local apropriada, sem enviar dados.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não se conecta de fato, apenas descobre qual interface IP usar.
        # '8.8.8.8' é o DNS do Google, 1 é uma porta arbitrária.
        # Nenhum dado é enviado, é apenas para simular uma conexão de saída
        # e assim o socket pode descobrir seu próprio IP local.
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' # Fallback para localhost se não conseguir determinar o IP
    finally:
        s.close()
    return IP
app = Flask(__name__)

# URL do seu backend
current_machine_ip = get_local_ip()
BACKEND_URL = os.getenv('BACKEND_URL', f'http://{current_machine_ip}:5000')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
    <!-- New Relic Browser Monitoring Snippet will be inserted here -->
    <!-- REPLACE THIS LINE WITH THE COMPLETE SNIPPET FROM YOUR NEW RELIC ACCOUNT -->
</head>
<body>
    <div class="container">
        <h1>📦 Gerenciamento de Produtos</h1>

        <div id="messages"></div>

        <!-- NOVOS BOTÕES PARA SIMULAR ERROS -->
        <div style="text-align: center; margin-bottom: 20px;">
            <button type="button" id="triggerBackendErrorBtn" style="background-color: #dc3545;">Simular Erro no Backend (500)</button>
            <button type="button" id="triggerFrontendErrorBtn" style="background-color: #ffc107; margin-left: 10px;">Simular Erro no Frontend (JS)</button>
        </div>
        <!-- FIM DOS NOVOS BOTÕES -->

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
                                <p class="price">R\$ ${parseFloat(product.price).toFixed(2)}</p>
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

        // --- NOVAS FUNÇÕES PARA SIMULAR ERROS ---
        async function triggerBackendError() {
            displayMessage('Disparando erro no backend...', 'loading');
            try {
                const response = await fetch(`${BACKEND_URL}/error-test`); // Chama a rota de erro do backend
                if (!response.ok) { // `response.ok` é false para status 4xx e 5xx
                    displayMessage(`Erro do Backend! Status: ${response.status}. Detalhes: ${await response.text().then(t => t.substring(0, 100)) + '...'}`, 'error');
                } else {
                    displayMessage(`Rota de erro chamada (resultado inesperado 200 OK): ${await response.text().then(t => t.substring(0, 100)) + '...'}`, 'success');
                }
            } catch (error) {
                console.error('Erro de rede ou CORS ao chamar rota de erro:', error);
                displayMessage(`Erro de conexão ou CORS: ${error.message}. Verifique o console.`, 'error');
            }
        }

        function triggerFrontendError() {
            displayMessage('Gerando erro JavaScript no frontend...', 'loading');
            try {
                // Isso causará um ReferenceError, pois 'nonExistentFunction' não está definida
                nonExistentFunction();
            } catch (e) {
                console.error('Erro JavaScript simulado:', e);
                displayMessage(`Erro JavaScript simulado: ${e.message}`, 'error');
            }
        }
        // --- FIM DAS NOVAS FUNÇÕES ---


        // Adiciona os event listeners aos formulários e botões
        addProductForm.addEventListener('submit', addProduct);
        searchProductForm.addEventListener('submit', searchProducts);
        clearSearchButton.addEventListener('click', clearSearch);

        // Adiciona event listeners para os novos botões
        document.getElementById('triggerBackendErrorBtn').addEventListener('click', triggerBackendError);
        document.getElementById('triggerFrontendErrorBtn').addEventListener('click', triggerFrontendError);

        // Carrega os produtos ao iniciar a página
        document.addEventListener('DOMContentLoaded', () => fetchProducts());

        // --- TRÁFEGO AUTOMÁTICO (Opcional, mas recomendado para simulação) ---
        setInterval(() => {
            const actions = [
                { func: () => fetchProducts(), weight: 0.6 },         // 60% listar/buscar produtos
                { func: triggerBackendError, weight: 0.3 },           // 30% simular erro no backend
                { func: triggerFrontendError, weight: 0.1 }           // 10% simular erro no frontend
            ];

            // Escolhe uma ação com base nos pesos
            const totalWeight = actions.reduce((sum, a) => sum + a.weight, 0);
            let randomNum = Math.random() * totalWeight;

            for (let i = 0; i < actions.length; i++) {
                if (randomNum < actions[i].weight) {
                    actions[i].func();
                    break;
                }
                randomNum -= actions[i].weight;
            }
        }, 7000); // Executa uma ação a cada 7 segundos (ajuste conforme a necessidade)
        // --- FIM DO TRÁFEGO AUTOMÁTICO ---
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Endpoint principal para exibir a interface de gerenciamento de produtos."""
    return render_template_string(HTML_TEMPLATE, BACKEND_URL=BACKEND_URL)

# Rota para teste de erro (mantida para observability)
@app.route('/error-test-frontend')
def error_test_frontend():
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