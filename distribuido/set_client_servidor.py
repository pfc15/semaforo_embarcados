import socket
import struct
import threading
import traceback
from time import sleep

class Cliente_sinal():
    def __init__(self, host="127.0.0.1", porta=65430):
        self.rodando = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, porta ))
        self._handles = {
            0x01: self.handle_abrir_sinal,
            0x02: self.handle_modo_dia
        }

        threading.Thread(
            target=self.receber_mensagens,
            args=(self.sock,),
            daemon=True
        ).start()

    def desligar(self):
        print("Encerrando servidor...")

        self.rodando = False

        try:
            self.sock.close()
        except:
            pass
        
        print("Servidor encerrado.")

    def receber_mensagens(self, sock):
        while self.rodando:
            try:
                data = sock.recv(1024)

                if not data:
                    print("Servidor desconectou")
                    break
                data = bytes(data)
                self._handles[data[0]](data[1:])

            except Exception as e:
                traceback.print_exc()
                break

        sock.close()

    def handle_modo_dia(self, data):
        print("handler modo dia")
        if data[0] == 0x00:
            print("modo noturno")
        elif data[0] == 0x01:
            print("modo dia")

    def handle_abrir_sinal(self, data):
        pass
    
    def enviar_msg(self, data):
        self.sock.send(data)
