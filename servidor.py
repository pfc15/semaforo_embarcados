import socket


HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

conn = socket.create_server((HOST, PORT))


soc, add = conn.accept()
while True:
    data = soc.recv(1024)
    
    print(f"endereço: {add} msg: {data}, tipo{type(data)}")
    soc.send(b'01101', 0)
