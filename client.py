from time import sleep
import datetime
import sys

DEBUG = False

if not DEBUG:
    import RPi.GPIO as GPIO


PINS_M1 = [17, 18, 23] # Semáforo M1 [b0, b1, b2]
PINS_M2 = [24, 8, 7] # Semáforo M2 [b0, b1, b2]
PINS_SW1 = [1, 12] # Botões de controle do semáforo M1
PINS_SW2 = [25, 22] # Botões de controle do semáforo M2

def setup():
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <m1|m2>")
        sys.exit(1)

    if DEBUG:
        print(f"Running in DEBUG mode. No GPIO setup will be performed.")
        return

    global PINS
    global ON
    global OFF
    global SW_PRINCIPAL
    global SW_TRAVESSIA


    # Configuração dos pinos GPIO output
    PINS = PINS_M1 if sys.argv[1] == "m1" else PINS_M2
    GPIO.setmode(GPIO.BCM)
    ON = GPIO.HIGH
    OFF = GPIO.LOW
    GPIO.setup(PINS, GPIO.OUT)

    # Configuração dos pinos GPIO input
    SW_PRINCIPAL = PINS_SW1[0] if sys.argv[1] == "m2" else PINS_SW2[0]
    SW_TRAVESSIA = PINS_SW1[1] if sys.argv[1] == "m2" else PINS_SW2[1]
   
    GPIO.setup(SW_PRINCIPAL, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(SW_PRINCIPAL, GPIO.FALLING, bouncetime=200)

    GPIO.setup(SW_TRAVESSIA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(SW_TRAVESSIA, GPIO.FALLING, bouncetime=200)

class Estado():
    def __init__(self, codigo, prox, temp_espera):
        self.codigo = codigo
        self.prox = prox
        self.temp_espera = temp_espera
    
    semaforo_da_vez = "principal"
    
class Estado0(Estado):
    def __init__(self):
        super().__init__(b"000", "E4", 1)

class Estado1(Estado):
    def __init__(self):
        super().__init__(b"001", "E1MinimoAtingido", 15)

    def principalPressed(self):
        self.prox = Estado3()
        return True

class Estado1MinimoAtingido(Estado):
    def __init__(self):
        super().__init__(b"001", "E3", 15)

class Estado3(Estado):
    def __init__(self):
        super().__init__(b"011", "E2", 1)
    
class Estado2(Estado):
    def __init__(self):
        super().__init__(b"010", "E3SegundaPiscada", 1)

class Estado3SegundaPiscada(Estado):
    def __init__(self):
        super().__init__(b"011", "E4", 1)

class Estado4(Estado):
    def __init__(self):
        super().__init__(b"100", "E5", 2)

class Estado5(Estado):
    def __init__(self):
        super().__init__(b"101", "E5MinimoAtingido", 5)

    def travessiaPressed(self):
        self.prox = "E7"
        return True
    
class Estado5MinimoAtingido(Estado):
    def __init__(self):
        super().__init__(b"101", "E7", 5)

class Estado7(Estado):
    def __init__(self):
        super().__init__(b"111", "E6", 1)

class Estado6(Estado):
    def __init__(self):
        super().__init__(b"110", "E7SegundaPiscada", 1)

class Estado7SegundaPiscada(Estado):
    def __init__(self):
        super().__init__(b"111", "E4", 1)

class Semaforo():
    semaforo_da_vez = "principal" # "principal" ou "travessia"
    standby = False
    
    def __init__(self):
        self.estados = {
            "E0": Estado0(),
            "E1": Estado1(),
            "E1MinimoAtingido": Estado1MinimoAtingido(),
            "E3": Estado3(),
            "E2": Estado2(),
            "E3SegundaPiscada": Estado3SegundaPiscada(),
            "E4": Estado4(),
            "E5": Estado5(),
            "E5MinimoAtingido": Estado5MinimoAtingido(),
            "E7": Estado7(),
            "E6": Estado6(),
            "E7SegundaPiscada": Estado7SegundaPiscada()
        }

        self.estado = self.estados["E1"]


    def mudaEstado(self, proximo_estado):
        if self.standby:
            if (isinstance(self.estado, Estado0)):
                self.estado.prox = "E4"
                self.estado.temp_espera = 1
            
            if (isinstance(self.estado, Estado4)):
                self.estado.prox = "E0"
                self.estado.temp_espera = 1

        if isinstance(self.estado, Estado4):
            if self.semaforo_da_vez == "principal":
                self.semaforo_da_vez = "travessia"
                self.estados["E4"].prox = "E1"
            else:
                self.semaforo_da_vez = "principal"
                self.estados["E4"].prox = "E5"
        
        self.estado = self.estados[proximo_estado]


def get_end_time(temp_espera):
    return datetime.datetime.now() + datetime.timedelta(seconds=temp_espera)

def set_gpio_output(codigo):
    if DEBUG:
        print(f"GPIO output for estado {codigo}: {codigo}")
        return

    # Mapear os estados para os padrões de saída GPIO
    gpio_mapping = {
        b"000": [OFF, OFF, OFF],  # E0
        b"001": [ON, OFF, OFF],   # E1
        b"010": [OFF, ON, OFF],   # E2
        b"011": [ON, ON, OFF],    # E3
        b"100": [OFF, OFF, ON],   # E4
        b"101": [ON, OFF, ON],    # E5
        b"110": [OFF, ON, ON],    # E6
        b"111": [ON, ON, ON]      # E7
    }

    GPIO.output(PINS, gpio_mapping[codigo])

def main():
    setup()

    semaforo = Semaforo()
    end_time = get_end_time(semaforo.estado.temp_espera)
    set_gpio_output(semaforo.estado.codigo)
    print(f"Estado atual: {semaforo.estado.codigo}, próximo estado: {semaforo.estados[semaforo.estado.prox].codigo}, tempo de espera: {semaforo.estado.temp_espera} segundos")

    try:
        while True:
            if datetime.datetime.now() >= end_time:
                semaforo.mudaEstado(semaforo.estado.prox)
                end_time = get_end_time(semaforo.estado.temp_espera)
                print(f"Estado atual: {semaforo.estado.codigo}, próximo estado: {semaforo.estados[semaforo.estado.prox].codigo}, tempo de espera: {semaforo.estado.temp_espera} segundos")
                set_gpio_output(semaforo.estado.codigo)
            sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if not DEBUG:
            GPIO.cleanup()

if __name__ == "__main__":
    main()