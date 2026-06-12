import socket
import threading
import struct
from time import sleep


class Servidor():
    def __init__(self, host="0.0.0.0", porta=65430):
        self.rodando = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        self.server.bind((host, porta ))
        self.server.listen()
        self.clientes = []

        self.t_aceita_conexao = threading.Thread(
            target=self.aceitar_conexoes,
            args=(self.server,),
            daemon=True
        )
        self.t_aceita_conexao.start()

    def desligar(self):
        print("Encerrando servidor...")

        self.rodando = False

        for cliente in self.clientes:
            try:
                cliente.shutdown(socket.SHUT_RDWR)
                cliente.close()
            except:
                pass

        self.clientes.clear()

        try:
            self.server.close()
        except:
            pass
        

        print("Servidor encerrado.")


    def handle_multa(self, data):
        direcoes = [(1, "principal"), (1, "cruzamento"), (2, "principal")
                    , (2, "cruzamento")]
    
        sem_dir = data[0]
        semaforo, via = direcoes[int(sem_dir)]
        print(data)
        velocidade = struct.unpack("f", data[1:5])[0]
        print(f"carro acima da velocidade no semaforo {semaforo} " \
        f"via {via}\n; velocidade: {velocidade}")
    
    def handle_quantidade(self, data):
        print(f"quantidade de carros: {data[0]}")
    
    def tratar_cliente(self, sock, addr):
        print(f"Cliente conectado: {addr}")

        try:
            while self.rodando:
                try: 
                    data = sock.recv(1024)

                    if not data:
                        break
                    data = bytes(data)

                    print(f"{addr}: {data.decode()}")
                    if data[0] == 0x01:
                        self.handle_multa(data=data[1:])
                    elif data[0] == 0x02:
                        self.handle_quantidade(data=data[1:])

                except OSError:
                    print("não estamos aceitando mais mensagens")
                    break

        finally:
            print(f"Cliente desconectado: {addr}")
            self.clientes.remove(sock)
            sock.close()


    def aceitar_conexoes(self, server):
        while self.rodando:
            try:
                sock, addr = server.accept()

                self.clientes.append(sock)

                threading.Thread(
                    target=self.tratar_cliente,
                    args=(sock, addr),
                    daemon=True
                ).start()
            except OSError:
                print("parando de aceitar novas mensagens")
                server.close()
                return

    def enviar_para_todos(self, msg):
        # dados = msg.decode()

        for cliente in self.clientes[:]:
            try:
                cliente.sendall(msg)
            except:
                self.clientes.remove(cliente)
                cliente.close()

    def enviar_modo(self, modo_dia:bool) -> bool:
        payload = bytes([0x02, 0x00 if not modo_dia else 0x01])
        self.enviar_para_todos(payload)
    
    def enviar_abrir(self, sinal:hex):
        payload = bytes([0x01, sinal])
        self.enviar_para_todos(payload)
    
    def enviar_acabou_emergencia(self):
        payload = bytes([0x03, 0x00])
        self.enviar_para_todos(payload)
    

def enviar_comandos_lentamente(servidor):
    cont = 0
    while servidor.rodando:
        sleep(5)
        if cont%2==0:
            servidor.enviar_modo(True)
        else:
            servidor.enviar_abrir(0x01)
        
        cont +=1



if __name__ =="__main__":
    servidor = Servidor()
    t = threading.Thread(
                target=enviar_comandos_lentamente,
                args=(servidor,),
                daemon=True
    )
    t.start()

    while True:
        texto = input("> ")
        if texto == "sair" or texto =="exit":
            servidor.desligar()
            break
        servidor.enviar_para_todos(texto)
