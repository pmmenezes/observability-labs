import requests
import random
import time
import json
from datetime import datetime

# URL do seu backend Flask de produtos
BACKEND_URL = "http://localhost:5000"

# Lista para armazenar os IDs dos produtos adicionados, para que possamos deletá-los depois
product_ids = []

# --- Funções para Interagir com a API ---
def add_random_product():
    """Adiciona um produto aleatório ao backend."""
    name_prefix = random.choice(["Smartphone", "Notebook", "Teclado", "Mouse", "Monitor", "Câmera", "Fone de Ouvido", "Smartwatch"])
    description_suffix = random.choice(["de última geração", "ergonômico", "com alta resolução", "para gamers", "compacto", "com bateria duradoura"])
    
    name = f"{name_prefix} {random.randint(100, 999)} - {datetime.now().strftime('%H%M%S')}"
    description = f"Um {name_prefix.lower()} {description_suffix}. Ótima performance e durabilidade."
    price = round(random.uniform(20.00, 2000.00), 2)

    product_data = {
        "name": name,
        "description": description,
        "price": price
    }

    # Ajustado para remover a necessidade de escapar o $
    print(f"Tentando adicionar: {product_data['name']} (R\${product_data['price']})")
    
    try:
        response = requests.post(f"{BACKEND_URL}/products", json=product_data)
        response.raise_for_status()  # Levanta um erro para status HTTP ruins (4xx ou 5xx)
        result = response.json()
        print(f"Produto adicionado com sucesso! ID: {result.get('id')}")
        if result.get('id'):
            product_ids.append(result['id']) # Adiciona o ID para futuras deleções
            # Manter a lista de IDs em um tamanho razoável
            if len(product_ids) > 50: # Limita para não consumir muita memória
                product_ids.pop(0)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao adicionar produto: {e}")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON na resposta de adição: {response.text}")

def search_and_list_products():
    """Pesquisa ou lista todos os produtos aleatoriamente."""
    search_term = ""
    # 70% de chance de pesquisar por um termo, 30% de listar todos
    if random.random() < 0.7: 
        # Escolhe um termo de busca comum ou um termo aleatório
        common_terms = ["Monitor", "Teclado", "Mouse", "Gamer", "UltraWide", "Full HD", "USB"]
        search_term = random.choice(common_terms + ["ProdutoInexistente", "XYZ", "Teste"])
        print(f"Pesquisando produtos com termo: '{search_term}'")
        url = f"{BACKEND_URL}/products?search={search_term}"
    else:
        print("Listando todos os produtos.")
        url = f"{BACKEND_URL}/products"

    try:
        response = requests.get(url)
        response.raise_for_status()
        products = response.json()
        print(f"Encontrados {len(products)} produtos.")
        # Opcional: printar os primeiros 3 produtos para verificação
        # for i, product in enumerate(products[:3]):
        #     print(f"  - ID: {product['id']}, Nome: {product['name']}, Preço: {product['price']}")
        # if len(products) > 3:
        #     print("  ...")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao pesquisar/listar produtos: {e}")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON na resposta de pesquisa: {response.text}")


def delete_random_product():
    """Deleta um produto aleatório da lista de IDs conhecidos."""
    if not product_ids:
        print("Nenhum produto conhecido para deletar. Adicione mais produtos primeiro.")
        return

    product_id_to_delete = random.choice(product_ids)
    print(f"Tentando deletar produto com ID: {product_id_to_delete}")

    try:
        response = requests.delete(f"{BACKEND_URL}/products/{product_id_to_delete}")
        response.raise_for_status()
        result = response.json()
        print(f"Resposta de deleção: {result.get('message', result)}")
        if "deletado com sucesso" in result.get('message', '').lower():
            # Remove o ID da lista apenas se a deleção foi bem-sucedida no backend
            if product_id_to_delete in product_ids:
                product_ids.remove(product_id_to_delete)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao deletar produto: {e}")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON na resposta de deleção: {response.text}")


def trigger_backend_error():
    """Dispara a rota de erro no backend para testar a captura de erros no New Relic."""
    print("Disparando rota de erro no backend (/error-test)...")
    try:
        response = requests.get(f"{BACKEND_URL}/error-test")
        print(f"Resposta da rota de erro (esperado erro 500): {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar rota de erro (esperado): {e}")

# --- FUNÇÃO PARA CHAMAR A ROTA DE LENTIDÃO ---
def call_slow_search_route():
    """Chama a rota de busca lenta no backend."""
    print("Chamando rota de busca lenta (/products/slow-search)...")
    try:
        response = requests.get(f"{BACKEND_URL}/products/slow-search")
        response.raise_for_status()
        products = response.json()
        print(f"Busca lenta concluída. Encontrados {len(products)} produtos.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar rota de busca lenta: {e}")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON na resposta de busca lenta: {response.text}")

# --- NOVA FUNÇÃO PARA SIMULAR ERROS DE DB ---
def trigger_db_error():
    """
    Chama a rota de simulação de erro de DB com um tipo de erro aleatório.
    Os tipos de erro devem corresponder aos definidos na rota '/products/db-error-test' do backend.
    """
    db_error_types = [
        'no_table',
        'unique_violation',
        'no_column',
        'syntax_error',
        'not_null_violation',
        'data_truncation'
    ]
    selected_error_type = random.choice(db_error_types)
    print(f"Simulando erro de DB: '{selected_error_type}' (/products/db-error-test?type={selected_error_type})...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/products/db-error-test?type={selected_error_type}")
        # Erros de DB devem resultar em status 500 ou 4xx, então raise_for_status() irá capturar
        response.raise_for_status() 
        # Esta linha geralmente não será alcançada se o erro de DB ocorrer como esperado
        print(f"Erro de DB '{selected_error_type}' não causou status de erro HTTP. Resposta: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        # requests.exceptions.HTTPError é uma subclasse de RequestException
        print(f"Erro de DB simulado '{selected_error_type}' capturado com sucesso (HTTP {e.response.status_code if e.response else 'N/A'}): {e}")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON na resposta de erro de DB: {response.text}")


# --- Loop Principal de Geração de Tráfego ---

def generate_traffic(num_iterations=None, sleep_min=1, sleep_max=3):
    """
    Gera tráfego para a aplicação backend.
    :param num_iterations: Número de iterações. Se None, executa indefinidamente.
    :param sleep_min: Tempo mínimo de pausa entre as operações (segundos).
    :param sleep_max: Tempo máximo de pausa entre as operações (segundos).
    """
    iteration = 0
    while True:
        iteration += 1
        print(f"\n--- Iteração {iteration} ---")

        # Ajuste os pesos para cada ação conforme o desejado
        actions = [
            (add_random_product, 0.30),         # 30% chance de adicionar
            (search_and_list_products, 0.40),   # 40% chance de pesquisar/listar
            (delete_random_product, 0.07),      # 7% chance de deletar
            (trigger_backend_error, 0.01),      # 1% chance de disparar um erro de código no backend
            (call_slow_search_route, 0.10),     # 10% chance de chamar a busca lenta (DB time)
            (trigger_db_error, 0.12)            # 12% chance de simular um erro de DB
        ]

        # Normaliza os pesos (garante que a soma é 1)
        total_weight = sum(a[1] for a in actions)
        normalized_weights = [a[1] / total_weight for a in actions]

        # Escolhe uma ação baseada nos pesos definidos
        action_func = random.choices([a[0] for a in actions], weights=normalized_weights, k=1)[0]
        action_func() # Chama a função de ação

        # Pausa aleatória
        sleep_time = random.uniform(sleep_min, sleep_max)
        print(f"Pausando por {sleep_time:.2f} segundos...")
        time.sleep(sleep_time)

        if num_iterations and iteration >= num_iterations:
            print(f"\nConcluídas {num_iterations} iterações.")
            break


if __name__ == "__main__":
    print(f"Iniciando gerador de tráfego para {BACKEND_URL}")
    print("Pressione Ctrl+C para parar a qualquer momento.")
    try:
        # Gerar tráfego indefinidamente (remova o comentário abaixo para limitar)
        generate_traffic() 
        
        # Exemplo para gerar 100 iterações e parar:
        # generate_traffic(num_iterations=100) 

    except KeyboardInterrupt:
        print("\nGerador de tráfego interrompido pelo usuário.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
