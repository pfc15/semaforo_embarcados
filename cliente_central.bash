#!/bin/bash

encerrar() {
    trap - SIGINT SIGTERM
    echo -e "\n[Ctrl+C detectado] Encerrando os semáforos..."
    # Envia o sinal de término para os PIDs guardados
    kill -- -$$ 2>/dev/null
    exit 0
}
trap encerrar SIGINT SIGTERM

python3 central/main_central.py &
PID_SERVIDOR=$!
sleep 2

python3 distribuido/set_client_servidor.py &
PID_CLIENTE=$!
sleep 2



wait $PID_SERVIDOR
wait $PID_CLIENTE