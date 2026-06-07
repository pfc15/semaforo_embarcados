import serial
import struct
from bitarray import bitarray
from central.modbus import *
from time import sleep
import time



def tirar_foto(ser, sensor:int) -> bool:
    if sensor>4 or sensor<=0:
        print("não existe esse sensor")
        return False
    endereco_sensor = [0, 0x11,0x12, 0x13, 0x14]
    isOk, _ = modbus_enviar_comando(
        ser, endereco_sensor[sensor], 0x10,
        bytes([
            0x01, 0x00,  # endereço
            0x01, 0x00,  # quantidade
            0x02,
            0x01, 0x00   # valor
        ])
    )
    if not isOk:
        print("erro no enivo do comando")
        return False
    tamanho, buffer = modbus_recebe_info(ser, False)
    print(f"buffer: {buffer}")

    isOk, _ = modbus_enviar_comando(
        ser, endereco_sensor[sensor], 0x03,
        bytes([
            0x00, 0x00,
            0x08, 0x00
        ])
    )

    tamanho, buffer = modbus_recebe_info(ser, False)
    print(f"buffer: {buffer}")
    if buffer[4] == 0x01:
        print("processando...")
    elif buffer[4] == 0x00:
        print("não recebeu comando")
        return False

    inicio = time.monotonic()
    while True:
        sleep(0.5)
        if time.monotonic() - inicio > 3.5:  
            print("time out")
            return False
        isOk, _ = modbus_enviar_comando(
        ser, endereco_sensor[sensor], 0x03,
        bytes([
            0x00, 0x00,
            0x08, 0x00
        ])
        )
        tamanho, buffer = modbus_recebe_info(ser, False)
        print(f"buffer: {buffer}")
        
        if tamanho<=0:
            print("sem mensagem")
            return False
        if buffer[4] == 0x01:
            print("processando...")
        elif buffer[4] == 0x00:
            print("não recebeu comando")
            return False
        elif buffer[4] == 0x03:
            print("ERRO AO TIRAR A FOTO")
            return False
        elif buffer[4] == 0x02:
            print("ok!")
            break
    placa = buffer[7:15].decode("ascii").rstrip("\x00")
    print(f"placa: {str(placa)}")
    confianca = int.from_bytes(buffer[15:17], 'big')
    print(f"confiança: {confianca}%")

    return True







# --- Exemplo de uso ---
if __name__ == "__main__":
    ser = setup()
    if ser is None:
        print("Falha ao abrir a porta serial.")
    else:
        sucesso = tirar_foto(ser, 1)
        print(f"Envio {'bem-sucedido' if sucesso else 'falhou'}")
        ser.close()