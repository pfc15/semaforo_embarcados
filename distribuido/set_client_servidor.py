import socket
import threading


def receber_mensagens(sock):
    while True:
        try:
            data = sock.recv(1024)

            if not data:
                print("Servidor desconectou")
                break

            print(data)
            for b in bytes(data):
                print(f"{hex(b)}", end="; ")
            print()

        except Exception as e:
            print(f"Erro: {e}")
            break

    sock.close()


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 65432))

threading.Thread(
    target=receber_mensagens,
    args=(sock,),
    daemon=True
).start()


while True:
    comando = input("> ")

    if comando == "sair":
        break

    sock.sendall(comando.encode())

sock.close()