
1 byte comando

Distribuido:
1 abrir_sinal(direção:1byte)
2 mudar_modo(modo:1byte) -> 0 modo_noturno; 1 modo_dia

central:
1 multa(semaforo_direcao:1 byte, velocidade:1 byte)
    semaforo 1; principal -> 0
    semaforo 1; cruzamento -> 1
    semaforo 2; principal -> 2
    semaforo 2; cruzamento -> 3
    
2 quantidade_carro(semaforo_direcao:1 byte, quantidade: 1byte)
