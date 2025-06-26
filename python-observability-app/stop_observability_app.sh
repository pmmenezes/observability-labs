#!/bin/bash

echo "*****************************************************"
echo "  Parando as aplicações Backend e Frontend..."
echo "*****************************************************"

# Verificar se lsof está instalado
if ! command -v lsof &> /dev/null; then
    echo "Erro: 'lsof' não encontrado. Por favor, instale com 'sudo apt install lsof'."
    exit 1
fi

# Parar o Backend (porta 5000)
echo "--- Tentando parar o Backend na porta 5000..."
PIDS_5000=$(sudo lsof -ti:5000)
if [ -n "$PIDS_5000" ]; then
    echo "   Processos encontrados na porta 5000: $PIDS_5000"
    sudo kill -9 $PIDS_5000
    echo "   Backend parado."
else
    echo "   Nenhum processo encontrado na porta 5000."
fi

# Parar o Frontend (porta 8000)
echo "--- Tentando parar o Frontend na porta 8000..."
PIDS_8000=$(sudo lsof -ti:8000)
if [ -n "$PIDS_8000" ]; then
    echo "   Processos encontrados na porta 8000: $PIDS_8000"
    sudo kill -9 $PIDS_8000
    echo "   Frontend parado."
else
    echo "   Nenhum processo encontrado na porta 8000."
fi

echo -e "\n*****************************************************"
echo "  Tentativa de parada das aplicações concluída."
echo "*****************************************************"
