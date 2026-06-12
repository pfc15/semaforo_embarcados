#!/bin/bash

encerrar() {
    trap - SIGINT SIGTERM
    echo -e "\n[Ctrl+C detectado] Encerrando os semáforos..."
    # Envia o sinal de término para os PIDs guardados
    kill -- -$$ 2>/dev/null
    exit 0
}
trap encerrar SIGINT SIGTERM
python3 distribuido/client.py &
PID_CLIENTE=$!

python3 central/main_central.py

kill $PID_CLIENTE

wait $PID_SERVIDOR