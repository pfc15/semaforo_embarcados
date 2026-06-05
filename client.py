from time import sleep
import datetime
import sys

DEBUG = False

if not DEBUG:
    import RPi.GPIO as GPIO


PINS_S1 = [17, 18, 23] # Semáforo S1 [b0, b1, b2]
PINS_S2 = [24, 8, 7] # Semáforo S2 [b0, b1, b2]

PINS_SW1 = [1, 12] # Botões de controle do semáforo S1
PINS_SW2 = [25, 22] # Botões de controle do semáforo S2

PINS_VEL_SENSOR1_S1 = [16, 20] 
PINS_VEL_SENSOR2_S1 = [21, 27]
PINS_VEL_SENSOR1_S2 = [11, 0]
PINS_VEL_SENSOR2_S2 = [5, 6]

ON = GPIO.HIGH
OFF = GPIO.LOW

LAST_TIME_SEM1_SENSOR1 = [None]
LAST_TIME_SEM1_SENSOR2 = [None]
LAST_TIME_SEM2_SENSOR1 = [None]
LAST_TIME_SEM2_SENSOR2 = [None]

class Client():
    def __init__(self):
        self.COUNT_CARS = 0

        self.semaforo1 = None
        self.semaforo2 = None
        self.modo_noite = True
        
    def setupGPIO(self):
        if DEBUG:
            print(f"Running in DEBUG mode. No GPIO setup will be performed.")
            return

        GPIO.setmode(GPIO.BCM)

    def setupGPIOSemaforo(self, semaforo="s1"):
        if DEBUG:
            print(f"Running in DEBUG mode. No GPIO setup will be performed.")
            return
        
        if semaforo == "s1":
            # Configuração dos pinos GPIO output (estado do semáforo 1)
            
            GPIO.setup(PINS_S1, GPIO.OUT)

            # Configuração dos pinos GPIO input (botões de controle semaforo 1)
            GPIO.setup(PINS_SW1[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(PINS_SW1[0], GPIO.FALLING, bouncetime=200)

            GPIO.setup(PINS_SW1[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(PINS_SW1[1], GPIO.FALLING, bouncetime=200)

            # Configuração dos pinos GPIO input (sensores de velocidade)
            GPIO.setup(PINS_VEL_SENSOR1_S1[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR1_S1[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR2_S1[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR2_S1[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            GPIO.add_event_detect(PINS_VEL_SENSOR1_S1[0], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR1_S1[1], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S1[0], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S1[1], GPIO.RISING, bouncetime=100, callback=velocidade_callback)

        if semaforo == "s2":
            # Configuração dos pinos GPIO output (estado do semáforo 2)
            GPIO.setup(PINS_S2, GPIO.OUT)

            # Configuração dos pinos GPIO input (botões de controle semaforo 2)
            GPIO.setup(PINS_SW2[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(PINS_SW2[0], GPIO.FALLING, bouncetime=200)

            GPIO.setup(PINS_SW2[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(PINS_SW2[1], GPIO.FALLING, bouncetime=200)

            # Configuração dos pinos GPIO input (sensores de velocidade)
            GPIO.setup(PINS_VEL_SENSOR1_S2[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR1_S2[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR2_S2[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PINS_VEL_SENSOR2_S2[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            GPIO.add_event_detect(PINS_VEL_SENSOR1_S2[0], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR1_S2[1], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S2[0], GPIO.RISING, bouncetime=100, callback=velocidade_callback)
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S2[1], GPIO.RISING, bouncetime=100, callback=velocidade_callback)

            

    def setupSem(self, semaforo="s1"):
        instanceSemaforo = Semaforo()

        if semaforo == "s1":
            self.semaforo1 = instanceSemaforo
        else:
            self.semaforo2 = instanceSemaforo

        if self.modo_noite:
            instanceSemaforo.estado = instanceSemaforo.estados["E4ModoNoite"]

        instanceSemaforo.end_time = get_end_time(instanceSemaforo.estado.temp_espera)

        set_gpio_output(instanceSemaforo.estado.codigo, semaforo=1 if semaforo == "s1" else 2)

    def loopSem(self, semaforo="s1"):
        instanceSemaforo = self.semaforo1 if semaforo == "s1" else self.semaforo2
        end_time = instanceSemaforo.end_time
        swpins = PINS_SW1 if semaforo == "s1" else PINS_SW2

        if not self.modo_noite:
            if GPIO.event_detected(swpins[0]):
                print("Botão principal pressionado!")
                if instanceSemaforo.estado.principalPressed():                
                    pass

            if GPIO.event_detected(swpins[1]):
                print("Botão de travessia pressionado!")
                if instanceSemaforo.estado.travessiaPressed():
                    pass

        if datetime.datetime.now() >= end_time:
            instanceSemaforo.mudaEstado(modo_noite=self.modo_noite)
            instanceSemaforo.end_time = get_end_time(instanceSemaforo.estado.temp_espera)
            set_gpio_output(instanceSemaforo.estado.codigo, semaforo=1 if semaforo == "s1" else 2)

class Estado():
    def __init__(self, codigo, prox, temp_espera):
        self.codigo = codigo
        self.prox = prox
        self.temp_espera = temp_espera
    
    semaforo_da_vez = "principal"

    def principalPressed(self):
        return False
    
    def travessiaPressed(self):
        return False
    
class Estado0(Estado):
    def __init__(self):
        super().__init__(b"000", "E4ModoNoite", 1)

class Estado1(Estado):
    def __init__(self):
        super().__init__(b"001", "E1MinimoAtingido", 15)

    def principalPressed(self):
        self.prox = "E3"
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

class Estado4ModoNoite(Estado):
    def __init__(self):
        super().__init__(b"100", "E0", 1)

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

    def __init__(self):
        self.estados = {
            "E0": Estado0(),
            "E1": Estado1(),
            "E1MinimoAtingido": Estado1MinimoAtingido(),
            "E3": Estado3(),
            "E2": Estado2(),
            "E3SegundaPiscada": Estado3SegundaPiscada(),
            "E4": Estado4(),
            "E4ModoNoite": Estado4ModoNoite(),
            "E5": Estado5(),
            "E5MinimoAtingido": Estado5MinimoAtingido(),
            "E7": Estado7(),
            "E6": Estado6(),
            "E7SegundaPiscada": Estado7SegundaPiscada()
        }

        self.estado = self.estados["E1"]
        self.end_time = None

    def mudaEstado(self, modo_noite=False):
        if modo_noite:
            if not (isinstance(self.estado, Estado0) or isinstance(self.estado, Estado4ModoNoite)):
                self.estado = self.estados["E4ModoNoite"]
                self.estado.end_time = get_end_time(self.estado.temp_espera)

        if not modo_noite:
            if isinstance(self.estado, Estado4ModoNoite) or isinstance(self.estado, Estado0):
                self.estado = self.estados["E1"]
                self.estado.end_time = get_end_time(self.estado.temp_espera)

        if isinstance(self.estado, Estado4):
            if self.semaforo_da_vez == "principal":
                self.semaforo_da_vez = "travessia"
                self.estados["E4"].prox = "E1"
            else:
                self.semaforo_da_vez = "principal"
                self.estados["E4"].prox = "E5"
        
        self.estado = self.estados[self.estado.prox]


def get_end_time(temp_espera):
    return datetime.datetime.now() + datetime.timedelta(seconds=temp_espera)

def set_gpio_output(codigo, semaforo=1):
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

    GPIO.output(PINS_S1 if semaforo == 1 else PINS_S2, gpio_mapping[codigo])

def velocidade_callback(channel):
    pinos_a = {
        PINS_VEL_SENSOR1_S1[0]: LAST_TIME_SEM1_SENSOR1,
        PINS_VEL_SENSOR2_S1[0]: LAST_TIME_SEM1_SENSOR2,
        PINS_VEL_SENSOR1_S2[0]: LAST_TIME_SEM2_SENSOR1,
        PINS_VEL_SENSOR2_S2[0]: LAST_TIME_SEM2_SENSOR2,
    }

    pinos_b = {
        PINS_VEL_SENSOR1_S1[1]: LAST_TIME_SEM1_SENSOR1,
        PINS_VEL_SENSOR2_S1[1]: LAST_TIME_SEM1_SENSOR2,
        PINS_VEL_SENSOR1_S2[1]: LAST_TIME_SEM2_SENSOR1,
        PINS_VEL_SENSOR2_S2[1]: LAST_TIME_SEM2_SENSOR2
    }

    name_bind = {pino: i + 1 for i, pino in enumerate(pinos_b)}

    if channel in pinos_a:
        pinos_a[channel][0] = datetime.datetime.now()
    elif channel in pinos_b:
        last_time_a = pinos_b[channel][0]
        if last_time_a is None:
            print(f"Falha ao calcular a velocidade para o canal {channel}.")
            return
        
        tempo_decorrido = (datetime.datetime.now() - last_time_a).total_seconds()
        if tempo_decorrido > 0:
            vel = 7.2 / tempo_decorrido
            print(f"Velocidade sensor {name_bind[channel]}: {vel:.2f} km/h, tempo decorrido: {tempo_decorrido:.2f} segundos")
        
        pinos_b[channel][0] = None

def main():
    client = Client()
    client.setupGPIO()
    client.setupGPIOSemaforo("s1")
    client.setupGPIOSemaforo("s2")
    client.setupSem("s1")
    client.setupSem("s2")

    try:
        while True:
            client.loopSem("s1")
            client.loopSem("s2")

            sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        if not DEBUG:
            GPIO.cleanup()

if __name__ == "__main__":
    main()