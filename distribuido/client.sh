#!/bin/bash

# Função que será executada quando você der Ctrl+C
encerrar() {
    echo -e "\n[Ctrl+C detectado] Encerrando os semáforos..."
    # Envia o sinal de término para os PIDs guardados
    kill $PID_M1 $PID_M2 2>/dev/null
    exit 0
}

# Captura o sinal SIGINT (Ctrl+C) e chama a função encerrar
trap encerrar SIGINT

# Inicia o cliente para o semáforo M1
python3 client.py m1 &
PID_M1=$!

# Inicia o cliente para o semáforo M2
python3 client.py m2 &
PID_M2=$!

echo "Processos iniciados!"
echo "M1 rodando no PID: $PID_M1"
echo "M2 rodando no PID: $PID_M2"
echo "Pressione Ctrl+C para parar ambos."

# Mantém o script rodando e aguardando os filhos
wait $PID_M1 $PID_M2