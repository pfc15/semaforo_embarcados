# Como rodar o projeto

Este projeto é iniciado pelo script [cliente_central.bash](cliente_central.bash), que abre o cliente distribuído e, em seguida, executa a central.

## Requisitos

- Python 3
- Ambiente Linux com permissões para executar scripts bash
- Para execução real em Raspberry Pi: biblioteca RPi.GPIO
- Se você estiver testando em um computador sem GPIO, ajuste a variável DEBUG para True em [distribuido/client.py](distribuido/client.py)

## Passo a passo



1. Ative o ambiente virtual, se estiver usando um:
   ```bash
   source venv/bin/activate
   ```

3. Dê permissão de execução ao script:
   ```bash
   chmod +x cliente_central.bash
   ```

4. Execute o programa:
   ```bash
   ./cliente_central.bash
   ```

## O que esse script faz

O script [cliente_central.bash](cliente_central.bash) executa:

1. o cliente distribuído em segundo plano com:
   ```bash
   python3 distribuido/client.py
   ```
2. a central principal em primeiro plano com:
   ```bash
   python3 central/main_central.py
   ```
3. ao final, encerra o processo do cliente.

## Observações

- Para parar a execução, digite 5 no menu do terminal.
- Se aparecer erro relacionado a RPi.GPIO, o projeto está sendo executado em um ambiente sem hardware de semáforo; nesse caso, use o modo de depuração em [distribuido/client.py](distribuido/client.py).

