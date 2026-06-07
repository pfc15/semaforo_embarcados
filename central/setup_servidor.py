import socket
import threading
from time import sleep


class servidor_central():
    def __init__(self, host="0.0.0.0", porta=65432):
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

    
    def tratar_cliente(self, sock, addr):
        print(f"Cliente conectado: {addr}")

        try:
            while self.rodando:
                try: 
                    data = sock.recv(1024)

                    if not data:
                        break

                    print(f"{addr}: {data.decode()}")
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

    def enviar_para_todos(self, msg: str):
        dados = msg.encode()

        for cliente in self.clientes[:]:
            try:
                cliente.sendall(dados)
            except:
                self.clientes.remove(cliente)
                cliente.close()

    

def enviar_comandos_lentamente(servidor):
    cont = 0
    while servidor.rodando:
        sleep(5)
        servidor.enviar_para_todos(f"enviei {cont}")
        cont +=1



if __name__ =="__main__":
    servidor = servidor_central()
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
