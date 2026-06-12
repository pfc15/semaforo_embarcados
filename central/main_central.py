import struct
from modbus import *
from setup_servidor import *
from time import sleep
import datetime
import time
from multa import *

class Servidor_Central(Servidor):
    def __init__(self):
        super().__init__()
        self.ser = setup()
        self.modo_dia = True
        self.t_emergencia = threading.Thread(
            target=self.monitora_emergencia,
            args=(),
            daemon=True
        )
        self.t_emergencia.start()


    def handle_multa(self, data):
        multa = self.tirar_foto(data[0])
        multa.velocidade = struct.unpack("f", data[1:5])[0]
        multa.salvar()


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

        isOk, _ = modbus_enviar_comando(
            self.ser, endereco_sensor[sensor], 0x03,
            bytes([
                0x00, 0x00,
                0x08, 0x00
            ])
        )

        tamanho, buffer = modbus_recebe_info(self.ser, False)
        if buffer[4] == 0x00:
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
                break
        
        placa = buffer[7:15].decode("ascii").rstrip("\x00")
        confianca = int.from_bytes(buffer[15:17], 'big')
        retorno = Multa(placa, confianca, 0, sensor)

        return retorno

    def monitora_emergencia(self):
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

            if tamanho >4:
                emergencia_ativa = buffer[4]
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
                    cont = 0
                    for b in buffer:
                        print(f"{cont}: {b}")
                        cont+=1
                    inicio = datetime.datetime.now()

                    # loop da emergencia, só acaba se furar o tempo ou emergencia acabar
                    while datetime.datetime.now() - inicio < datetime.timedelta(seconds=25):
                        print("---"*25)
                        print("EMERGENCIA")
                        self.enviar_abrir(direcao)
                        sleep(2)
                        isOk, _ = modbus_enviar_comando(self.ser, 0x20, 0x03,
                        bytes([
                            0x00, 0x00,  # endereço inicial = 1
                            0x0B, 0x00    # quantidade = 11
                        ]))
                        if not isOk:
                            print("ERRO AO LER EMERGENCIA")
                            return False

                        tamanho, buffer = modbus_recebe_info(self.ser, False)
                        cont = 0
                        for b in buffer:
                            print(f"{cont}: {b}")
                            cont+=1
                        if tamanho>4:
                            emergencia_ativa = buffer[4]
                            if emergencia_ativa == 0x00:
                                break
                    
                    self.enviar_acabou_emergencia()


                if (modo == 0x00) != self.modo_dia:
                    self.modo_dia = True if modo == 0x00 else False
                    self.enviar_modo(self.modo_dia)


def menu(servidor:Servidor_Central):
    comando = 0
    
    while True:
        print("--"*25)
        print(" 1- abrir sinal")
        print(" 2- mudar modo")
        print(" 3- ver log de multas")
        print(" 4- ver passagem de carros")
        print(" 5- fechar aplicação ")
        try:
            comando = int(input("escolha sua opção: "))
            if comando == 1:
                subcomando =-1
                while subcomando<0 or subcomando>4:
                    print("""
1- via principal sinal leste
2- cruzamento sinal leste
3- via principal sinal oeste
4- cruzamento sinal oeste
""")   
                    subcomando = int(input("escolha sua opção: "))
                
                    servidor.enviar_abrir(subcomando)
                    
            elif comando == 2:
                subcomando =-1
                while subcomando<0 or subcomando>4:
                    print("""
1- modo noite
2- modo dia
""")   
                    subcomando = int(input("escolha sua opção: "))
                
                    servidor.enviar_abrir(subcomando-1)

            elif comando== 3:
                with open("log_multas.csv", "r") as fp:
                    texto = fp.read()
                    print("---"*25)
                    print("LOG MULTAS")
                    print(texto)
                    print("---"*25)
            
            elif comando == 4: # passagem de carros
                pass
                
            elif comando ==5:
                servidor.desligar()
                break

        except EOFError:
            break
        except :
            print("printe números apenas")
        
        

if __name__ == "__main__":
    servidor = Servidor_Central()
    menu(servidor)