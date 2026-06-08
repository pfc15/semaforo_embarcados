import datetime

class Multa():
    def __init__(self, placa, confianca, velocidade, camera):
        self.placa = placa
        self.confianca = confianca
        self.velocidade = velocidade
        self.camera = camera 
        self.timestamp = datetime.datetime.now()
    
    def salvar(self):
        with open("log_multas.csv", "+a") as w:
            w.write(f"{self.timestamp};{self.placa};{self.confianca};{self.velocidade};{self.camera}")
    
    def printar_multa(self):
        print(f"{self.timestamp};{self.placa};{self.confianca};{self.velocidade};{self.camera}")