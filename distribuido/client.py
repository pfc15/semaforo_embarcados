from time import sleep
import datetime
import sys
import set_client_servidor as s
import threading

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

STATE_BIND = {
    "principal": "E1EmergenciaPrincipal",
    "travessia1": "E5EmergenciaTravessia",
    "travessia2": "E5EmergenciaTravessia"
}

class Client():
    def __init__(self):
        self.COUNT_CARS = 0

        self.semaforo1 = None
        self.semaforo2 = None
        self.modo_noite = False
        self.modo_emergencia = None # "principal" | "travessia1" | "travessia2" | None
        self.client_server = s.Cliente_sinal() # Instancia o cliente de rede para comunicação com o servidor
        
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

            GPIO.add_event_detect(PINS_VEL_SENSOR1_S1[0], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR1_S1[1], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S1[0], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S1[1], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))

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

            GPIO.add_event_detect(PINS_VEL_SENSOR1_S2[0], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR1_S2[1], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S2[0], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))
            GPIO.add_event_detect(PINS_VEL_SENSOR2_S2[1], GPIO.RISING, callback=lambda channel: self.velocidade_callback(channel))

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

        # emergencia 
        if (
            self.modo_emergencia
            and not isinstance(
                instanceSemaforo.estado,
                (Estado1EmergenciaPrincipal, Estado5EmergenciaTravessia))
        ):
            pr = self.modo_emergencia == "principal"
            t1 = self.modo_emergencia == "travessia1"
            t2 = self.modo_emergencia == "travessia2"
            s1 = semaforo == "s1"
            s2 = semaforo == "s2"

            if ((pr and (s1 or s2)) or (s1 and t1) or (s2 and t2)):
                instanceSemaforo.estado = instanceSemaforo.estados[STATE_BIND[self.modo_emergencia]]
                instanceSemaforo.end_time = get_end_time(instanceSemaforo.estado.temp_espera)
                set_gpio_output(instanceSemaforo.estado.codigo, semaforo=1 if semaforo == "s1" else 2)

        if not self.modo_noite:
            if GPIO.event_detected(swpins[0]):
                if instanceSemaforo.estado.principalPressed():                
                    pass

            if GPIO.event_detected(swpins[1]):
                if instanceSemaforo.estado.travessiaPressed():
                    pass

        if datetime.datetime.now() >= end_time:
            instanceSemaforo.mudaEstado(modo_noite=self.modo_noite)
            instanceSemaforo.end_time = get_end_time(instanceSemaforo.estado.temp_espera)
            set_gpio_output(instanceSemaforo.estado.codigo, semaforo=1 if semaforo == "s1" else 2)

    def setModoEmergencia(self, modo):
        self.modo_emergencia = modo

    def handle_abrir_sinal(self, data):
        # semaforo 1; principal -> 0
        # semaforo 1; cruzamento -> 1
        # semaforo 2; principal -> 2
        # semaforo 2; cruzamento -> 3
        modes = {
            0x00: "E1",
            0x01: "E5",
            0x02: "E1",
            0x03: "E5"
        }


        estado = modes[data[0]-1]
        print(f"data: {data[0]-1}, estado: {estado}")

        if data[0]-1 == 0x00 or data[0]-1 == 0x01:
            self.semaforo1.estado = self.semaforo1.estados[estado]
            self.semaforo1.estado.end_time = get_end_time(self.semaforo1.estado.temp_espera)
        
        elif data[0]-1 == 0x02 or data[0]-1 == 0x03:
            self.semaforo2.estado = self.semaforo2.estados[estado]
            self.semaforo2.estado.end_time = get_end_time(self.semaforo2.estado.temp_espera)
        

        

    def handle_iniciar_emergencia(self, data):
        # semaforo 1; principal -> 0
        # semaforo 1; cruzamento -> 1
        # semaforo 2; principal -> 2
        # semaforo 2; cruzamento -> 3
        modes = {
            0x00: "principal",
            0x01: "travessia1",
            0x02: "principal",
            0x03: "travessia2"
        }

        self.setModoEmergencia(modes[data[0]-1])

    def handle_acabar_emergencia(self, data):
        self.setModoEmergencia(None)

    
    def handle_modo_dia(self, data):
        modes = {
            0x00: True,
            0x01: False
        }

        self.modo_noite = modes[data[0]]

    def velocidade_callback(self, channel):
        last_time_pins_a = {
            PINS_VEL_SENSOR1_S1[0]: LAST_TIME_SEM1_SENSOR1, # 
            PINS_VEL_SENSOR2_S1[0]: LAST_TIME_SEM1_SENSOR2,
            PINS_VEL_SENSOR1_S2[0]: LAST_TIME_SEM2_SENSOR1,
            PINS_VEL_SENSOR2_S2[0]: LAST_TIME_SEM2_SENSOR2,
        }

        last_time_pins_b = {
            PINS_VEL_SENSOR1_S1[1]: LAST_TIME_SEM1_SENSOR1,
            PINS_VEL_SENSOR2_S1[1]: LAST_TIME_SEM1_SENSOR2,
            PINS_VEL_SENSOR1_S2[1]: LAST_TIME_SEM2_SENSOR1,
            PINS_VEL_SENSOR2_S2[1]: LAST_TIME_SEM2_SENSOR2
        }

        name_bind = {pino: i + 1 for i, pino in enumerate(last_time_pins_b)}

        if channel in last_time_pins_a:
            last_time_pins_a[channel][0] = datetime.datetime.now()
            
        elif channel in last_time_pins_b:
            last_time_a = last_time_pins_b[channel][0]
            if last_time_a is None:
                print(f"Falha ao calcular a velocidade para o canal {channel}.")
                return
            
            tempo_decorrido = (datetime.datetime.now() - last_time_a).total_seconds()
            sensor = name_bind[channel]
            if tempo_decorrido > 0:
                vel = 9 / tempo_decorrido
                self.COUNT_CARS += 1
            
                if vel > 60:

                    self.client_server.enviar_msg(bytes([0x01, sensor, vel ])) # Enviar alerta de velocidade alta para o servidor


            last_time_pins_b[channel][0] = None

    def setupMonitoramentoVelocidadePassagens(self):
        threading.Thread(
            target=self.monitoraVelocidadePassagens,
            args=(),
            daemon=True
        ).start()

    def monitoraVelocidadePassagens(self):
        while True:
            self.client_server.enviar_msg(bytes([0x02, self.COUNT_CARS]))

            sleep(2)


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

class Estado1EmergenciaPrincipal(Estado):
    def __init__(self):
        super().__init__(b"001", "E1EmergenciaPrincipal", 1)

class Estado5EmergenciaTravessia(Estado):
    def __init__(self):
        super().__init__(b"101", "E5EmergenciaTravessia", 1)


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
            "E7SegundaPiscada": Estado7SegundaPiscada(),
            "E1EmergenciaPrincipal": Estado1EmergenciaPrincipal(),
            "E5EmergenciaTravessia": Estado5EmergenciaTravessia()
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


def main():
    sleep(5)
    print("-- COMEÇANDO CLIENTE --")
    client = Client() # Instancia o módulo físico do cliente (GPIO, botões, sensores, etc) e a lógica de controle dos semáforos
    client.setupGPIO()
    client.setupGPIOSemaforo("s1")
    client.setupGPIOSemaforo("s2")
    client.setupSem("s1")
    client.setupSem("s2")
    client.setupMonitoramentoVelocidadePassagens()

    client.client_server._handles = {
        0x01: client.handle_iniciar_emergencia,
        0x02: client.handle_modo_dia,
        0x03: client.handle_acabar_emergencia,
        0x04: client.handle_abrir_sinal
    }

    try:
        while True:
            client.loopSem("s1")
            client.loopSem("s2")

            sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        if not DEBUG:
            GPIO.cleanup()

if __name__ == "__main__":
    main()