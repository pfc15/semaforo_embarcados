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
        self.t_emergencia = threading.Thread(
            target=self.monitora_emergencia,
            args=(),
            daemon=True
        )
        self.t_emergencia.start()


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

    def monitora_emergencia(self):
        emergencia = False
        while self.rodando:
            isOk, _ = modbus_enviar_comando(self.ser, 0x20, 0x03,
            bytes([
                0x00, 0x00,  # endereço inicial = 1
                0x0B, 0x00    # quantidade = 11
            ]))
            if not isOk:
                print("ERRO AO LER EMERGENCIA")
                return False

            tamanho, buffer = modbus_recebe_info(self.ser, False)
            print("-="*25)
            print("emergencia")
            cont = 0
            for h in bytes(buffer):
                print(f"{cont}: {hex(h)}")
                cont+=1

            emergencia_ativa = buffer[4]
            estrada = buffer[6]
            direcao = buffer[8]
            intersecao_id = buffer[10]
            tipo_veiculo = buffer[12]
            signal_group = buffer[14]
            time_out = buffer[16]
            nao_atendidos = buffer[18]
            tempo_decorrido = buffer[20]
            tempo_max = buffer[22]
            modo = buffer[24]

            
            if emergencia_ativa == 0x01:
                print("---"*25)
                print("EMERGENCIA")
                self.enviar_abrir(direcao)  


# --- Exemplo de uso ---
if __name__ == "__main__":
    servidor = Servidor_Central()
    # t = threading.Thread(
    #             target=enviar_comandos_lentamente,
    #             args=(servidor,),
    #             daemon=True
    # )
    # t.start()

    while True:
        pass