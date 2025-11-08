import machine, time, ntptime, network, json, bmp280
from machine import I2C, Pin, ADC
from umqtt.robust import MQTTClient

SSID = "Internet"
PASSWORD = "12Abril2005"
MQTT_BROKER = 'test.mosquitto.org'
CLIENT_ID = 'jrevolorioesp8266'
TOPICO_CLIMA = 'umes/clima'

sensor = ADC(0)
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
bmp = bmp280.BMP280(i2c)

def conectarWifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Conectando a la red WiFi...")
        sta_if.active(True)
        sta_if.connect(SSID, PASSWORD)
        while not sta_if.isconnected():
            pass
    print("Conectado. IP:", sta_if.ifconfig()[0])

def sincronizarHora():
    try:
        ntptime.settime()
        print("Hora sincronizada con NTP")
    except:
        print("Error al sincronizar con NTP")

def obtenerHoraLocal():
    utc = time.localtime()
    ts = time.mktime(utc) - (6 * 3600)
    local = time.localtime(ts)
    return "{:02d}:{:02d}:{:02d}".format(local[3], local[4], local[5])

def obtenerFechaLocal():
    utc = time.localtime()
    ts = time.mktime(utc) - (6 * 3600)
    local = time.localtime(ts)
    return "{:04d}-{:02d}-{:02d}".format(local[0], local[1], local[2])

def calcularAltitud(presion, presion_mar=1013.25):
    return 44330 * (1 - (presion / presion_mar) ** 0.1903)

def obtenerTemperatura():
    try:
        return bmp.temperature
    except:
        return None

def obtenerPresion():
    try:
        return bmp.pressure / 100
    except:
        return None

def obtenerAltitud(presion):
    try:
        return calcularAltitud(presion)
    except:
        return None

def obtenerCalidadAire():
    lectura = sensor.read()
    calidad = max(0, min(100, 100 - int((lectura / 1023) * 100)))
    return calidad

def publicarDatos():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER)
        client.connect()
        print('Conectado al broker MQTT')
    except Exception as e:
        print("Error al conectar al broker:", e)
        return
    
    print('Inicializando dispositivo...')
    time.sleep(10)
    print('Dispositivo listo')

    while True:
        hora = obtenerHoraLocal()
        fecha = obtenerFechaLocal()
        temperatura = obtenerTemperatura()
        presion = obtenerPresion()
        altitud = obtenerAltitud(presion) if presion else None
        calidad = obtenerCalidadAire()

        clima = {
            "Fecha": fecha,
            "Hora": hora,
            "temperatura": temperatura,
            "presion": presion,
            "altitud": altitud,
            "calidadAire": calidad,
            "estacion": 1
        }

        jsonDataClima = json.dumps(clima)
        client.publish(TOPICO_CLIMA, jsonDataClima)
        print("Datos publicados:", jsonDataClima)
        time.sleep(600)

conectarWifi()
sincronizarHora()
publicarDatos()