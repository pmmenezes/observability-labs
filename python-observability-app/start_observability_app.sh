#!/bin/bash

# --- Variáveis de Configuração ---
# !!! ATENÇÃO: Estes valores devem ser consistentes com o seu app.py e o setup do Postgres !!!
DB_USER="appuser"
DB_PASS="apppassword" # Lembre-se de usar uma senha forte e segura em produção!
DB_NAME="appdb"
# PROJECT_ROOT aponta para o diretório onde este script está sendo executado
PROJECT_ROOT="$(pwd)"

# --- Detecção Dinâmica de IP e Exportação de BACKEND_URL ---
echo "Detectando endereço IP do host..."
# Tenta obter o primeiro endereço IPv4 da máquina.
# 'hostname -I' lista todos os endereços IP. 'awk '{print $1}' pega o primeiro.
# Isso geralmente funciona para a maioria dos cenários de rede (IPv4).
HOST_IP=$(hostname -I | awk '{print $1}')

if [ -z "$HOST_IP" ]; then
    echo "Aviso: Não foi possível detectar automaticamente o endereço IP do host."
    echo "Usando 'localhost' como fallback. Isso pode causar problemas se o acesso for de outra máquina."
    export BACKEND_URL="http://localhost:5000"
else
    echo "Endereço IP do Host Detectado: $HOST_IP"
    export BACKEND_URL="http://${HOST_IP}:5000"
fi

echo "O Frontend se comunicará com o Backend em: $BACKEND_URL"
# --- Fim da Detecção Dinâmica de IP ---


# --- Caminhos para os logs de cada aplicação ---
BACKEND_LOG="$PROJECT_ROOT/backend/backend.log"
FRONTEND_LOG="$PROJECT_ROOT/frontend/frontend.log"

echo "*****************************************************"
echo "  Iniciando a configuração do PostgreSQL e as aplicações Backend/Frontend..."
echo "*****************************************************"

# --- 0. Verificar dependências de sistema (lsof) ---
if ! command -v lsof &> /dev/null; then
    echo "   'lsof' não encontrado. Instalando..."
    sudo apt install -y lsof || { echo "Erro ao instalar 'lsof'. Por favor, instale manualmente ou verifique suas permissões de sudo."; exit 1; }
fi

# --- 1. Configurar PostgreSQL (Usuário e Banco de Dados) ---
echo -e "\n--- 1. Verificando e configurando usuário e banco de dados PostgreSQL..."

# Verificar e criar usuário PostgreSQL
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")
if [[ "$USER_EXISTS" != "1" ]]; then
    echo "   - Criando usuário '$DB_USER'..."
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || { echo "Erro ao criar usuário $DB_USER. Verifique as permissões de sudo ou se o PostgreSQL está rodando."; exit 1; }
else
    echo "   - Usuário '$DB_USER' já existe."
fi

# Verificar e criar banco de dados PostgreSQL
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
if [[ "$DB_EXISTS" != "1" ]]; then
    echo "   - Criando banco de dados '$DB_NAME'..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || { echo "Erro ao criar banco de dados $DB_NAME. Verifique as permissões de sudo."; exit 1; }
else
    echo "   - Banco de dados '$DB_NAME' já existe."
fi

echo "   - Concedendo privilégios ao usuário '$DB_USER' no banco de dados '$DB_NAME'..."
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" || { echo "Erro ao conceder privilégios."; exit 1; }

# --- 2. Inicializar banco de dados com dados de exemplo (do init.sql) ---
echo -e "\n--- 2. Executando 'database/init.sql' para criar tabelas e dados..."
# Exporta a senha para que o psql não solicite interativamente
export PGPASSWORD="$DB_PASS"
psql -h localhost -d "$DB_NAME" -U "$DB_USER" -f "$PROJECT_ROOT/database/init.sql" || { echo "Erro ao executar init.sql no banco de dados. Certifique-se que o arquivo existe e o PostgreSQL está acessível."; unset PGPASSWORD; exit 1; }
unset PGPASSWORD # Remove a variável de ambiente da senha
echo "   Banco de dados '$DB_NAME' inicializado/atualizado com sucesso."

# --- 3. Preparar e Iniciar Backend ---
echo -e "\n--- 3. Preparando e iniciando Backend (http://${HOST_IP}:5000)..."
cd "$PROJECT_ROOT/backend" || { echo "Erro: Não foi possível navegar para $PROJECT_ROOT/backend. Verifique a estrutura do diretório."; exit 1; }

# Cria ambiente virtual se não existir
if [ ! -d "venv_backend" ]; then
    echo "   - Criando ambiente virtual 'venv_backend'..."
    python3 -m venv venv_backend || { echo "Erro ao criar ambiente virtual para backend."; exit 1; }
fi

echo "   - Ativando ambiente virtual e instalando dependências do backend..."
source venv_backend/bin/activate || { echo "Erro ao ativar ambiente virtual para backend."; exit 1; }
pip install -r requirements.txt || { echo "Erro ao instalar dependências do backend."; exit 1; }

# Garante que qualquer instância anterior na porta 5000 seja parada
echo "   - Verificando e encerrando processos anteriores na porta 5000..."
sudo lsof -ti:5000 | xargs sudo kill -9 2>/dev/null
sleep 1 # Pequena pausa para a porta liberar


echo "   - Iniciando Backend em segundo plano (logs em $BACKEND_LOG)..."
NEW_RELIC_CONFIG_FILE="./newrelic.ini"  newrelic-admin run-program python3 app.py > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$! # Captura o PID do processo em background
echo "   Backend iniciado com PID: $BACKEND_PID"
deactivate
cd "$PROJECT_ROOT" # Volta para a raiz do projeto

# Aguarda um momento para o backend inicializar completamente antes do frontend tentar conectar
echo "   Aguardando 5 segundos para o Backend inicializar completamente..."
sleep 5

# --- 4. Preparar e Iniciar Frontend ---
echo -e "\n--- 4. Preparando e iniciando Frontend (http://${HOST_IP}:8000)..."
cd "$PROJECT_ROOT/frontend" || { echo "Erro: Não foi possível navegar para $PROJECT_ROOT/frontend. Verifique a estrutura do diretório."; exit 1; }

# Cria ambiente virtual se não existir
if [ ! -d "venv_frontend" ]; then
    echo "   - Criando ambiente virtual 'venv_frontend'..."
    python3 -m venv venv_frontend || { echo "Erro ao criar ambiente virtual para frontend."; exit 1; }
fi

echo "   - Ativando ambiente virtual e instalando dependências do frontend..."
source venv_frontend/bin/activate || { echo "Erro ao ativar ambiente virtual para frontend."; exit 1; }
pip install -r requirements.txt || { echo "Erro ao instalar dependências do frontend."; exit 1; }

# Garante que qualquer instância anterior na porta 8000 seja parada
echo "   - Verificando e encerrando processos anteriores na porta 8000..."
sudo lsof -ti:8000 | xargs sudo kill -9 2>/dev/null
sleep 1 # Pequena pausa para a porta liberar

echo "   - Iniciando Frontend em segundo plano (logs em $FRONTEND_LOG)..."
NEW_RELIC_CONFIG_FILE="./newrelic.ini"  newrelic-admin run-program python3 app.py > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$! # Captura o PID do processo em background
echo "   Frontend iniciado com PID: $FRONTEND_PID"
deactivate
cd "$PROJECT_ROOT" # Volta para a raiz do projeto

echo -e "\n*****************************************************"
echo "  🎉 Configuração e inicialização da aplicação concluídas! 🎉"
echo "  - Acesse o Frontend em:   http://${HOST_IP}:8000"
echo "  - O Backend está em:      http://${HOST_IP}:5000"
echo ""
echo "  Para verificar os logs em tempo real:"
echo "  - Backend:  tail -f $BACKEND_LOG"
echo "  - Frontend: tail -f $FRONTEND_LOG"
echo ""
echo "  Para parar as aplicações, execute: ./stop_observability_app.sh"
echo "*****************************************************"
