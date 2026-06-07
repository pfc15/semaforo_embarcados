import struct
from modbus import *
from setup_servidor import *
from time import sleep
import time
from multa import *

class Servidor_Central(Servidor):
    def __init__(self):
        super().__init__()
        self.ser = setup()
    
    def handle_multa(self, data):
        print('-='*25)
        print("multa")
        multa = self.tirar_foto(data[0])
        multa.velocidade = struct.unpack("f", data[1:5])[0]
        multa.printar_multa()
        multa.salvar()
        print("multa, salva")


    def tirar_foto(self, sensor:int) ->  Multa:
        if sensor>4 or sensor<=0:
            print("não existe esse sensor")
            return None
        endereco_sensor = [0, 0x11,0x12, 0x13, 0x14]
        isOk, _ = modbus_enviar_comando(
            self.ser, endereco_sensor[sensor], 0x10,
            bytes([
                0x01, 0x00,  # endereço
                0x01, 0x00,  # quantidade
                0x02,
                0x01, 0x00   # valor
            ])
        )
        if not isOk:
            print("erro no enivo do comando")
            return None
        tamanho, buffer = modbus_recebe_info(self.ser, False)
        print(f"buffer: {buffer}")

        isOk, _ = modbus_enviar_comando(
            self.ser, endereco_sensor[sensor], 0x03,
            bytes([
                0x00, 0x00,
                0x08, 0x00
            ])
        )

        tamanho, buffer = modbus_recebe_info(self.ser, False)
        print(f"buffer: {buffer}")
        if buffer[4] == 0x01:
            print("processando...")
        elif buffer[4] == 0x00:
            print("não recebeu comando")
            return None

        inicio = time.monotonic()
        while True:
            sleep(0.5)
            if time.monotonic() - inicio > 3.5:  
                print("time out")
                return None
            isOk, _ = modbus_enviar_comando(
            self.ser, endereco_sensor[sensor], 0x03,
            bytes([
                0x00, 0x00,
                0x08, 0x00
            ])
            )
            tamanho, buffer = modbus_recebe_info(self.ser, False)
            print(f"buffer: {buffer}")
            
            if tamanho<=0:
                print("sem mensagem")
                return None
            if buffer[4] == 0x01:
                print("processando...")
            elif buffer[4] == 0x00:
                print("não recebeu comando")
                return None
            elif buffer[4] == 0x03:
                print("ERRO AO TIRAR A FOTO")
                return None
            elif buffer[4] == 0x02:
                print("ok!")
                break
        
        placa = buffer[7:15].decode("ascii").rstrip("\x00")
        print(f"placa: {str(placa)}")
        confianca = int.from_bytes(buffer[15:17], 'big')
        print(f"confiança: {confianca}%")
        retorno = Multa(placa, confianca, 0, sensor)

        return retorno


# --- Exemplo de uso ---
if __name__ == "__main__":
    servidor = Servidor_Central()
    t = threading.Thread(
                target=enviar_comandos_lentamente,
                args=(servidor,),
                daemon=True
    )
    t.start()

    while True:
        pass