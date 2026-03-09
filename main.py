import machine
import time
import WIFI_CONFIG
from ota import OTAUpdater

# =========================
# CONFIGURACIÓN OTA
# =========================
REPO_URL       = "https://github.com/patinojuan2002-ops/Juan-OTA/"
CHECK_INTERVAL = 60  # segundos entre chequeos

# =========================
# LED integrado
# =========================
led = machine.Pin("LED", machine.Pin.OUT)

# =========================
# UART RS485
# =========================
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

def send_modbus_query(query):
    uart.write(query)
    time.sleep(0.3)
    return uart.read()

# =========================
# TIMER LED SIMPLE
# =========================
led_timer = machine.Timer()

def led_toggle(timer):
    led.toggle()

def led_start(period_ms=300):
    led_timer.init(period=period_ms, mode=machine.Timer.PERIODIC, callback=led_toggle)

def led_stop():
    led_timer.deinit()
    led.value(0)

# =========================
# TRAMAS MODBUS
# =========================
Q_PH       = bytes([0x01,0x03,0x00,0x06,0x00,0x01,0x64,0x0B])
Q_HUM_TEMP = bytes([0x01,0x03,0x00,0x12,0x00,0x02,0x64,0x0E])
Q_EC       = bytes([0x01,0x03,0x00,0x15,0x00,0x01,0x95,0xCE])
Q_NPK      = bytes([0x01,0x03,0x00,0x1E,0x00,0x03,0x65,0xCD])

# =========================
# CHEQUEO OTA
# =========================
def check_and_update():
    print("Chequeando actualizaciones...")
    try:
        ota = OTAUpdater(WIFI_CONFIG.SSID, WIFI_CONFIG.PASSWORD, REPO_URL, "main.py")
        ota.download_and_install_update_if_available()
        # Si hay update, la Pico se reinicia sola dentro del OTAUpdater
        # Si no hay update, continúa normalmente
    except Exception as e:
        print("Error OTA:", e)

# =========================
# LECTURA DEL SENSOR
# =========================
def leer_sensor():
    led_start()

    r = send_modbus_query(Q_PH)
    ph = ((r[3] << 8) | r[4]) / 100 if r else None

    r = send_modbus_query(Q_HUM_TEMP)
    if r and len(r) >= 7:
        hum  = ((r[3] << 8) | r[4]) / 10
        temp = ((r[5] << 8) | r[6]) / 10
    else:
        hum = temp = None

    r = send_modbus_query(Q_EC)
    ec = (r[3] << 8) | r[4] if r else None

    r = send_modbus_query(Q_NPK)
    if r and len(r) >= 9:
        n = (r[3] << 8) | r[4]
        p = (r[5] << 8) | r[6]
        k = (r[7] << 8) | r[8]
    else:
        n = p = k = None

    led_stop()

    print("pH:", ph)
    print("Humedad:", hum, "%")
    print("Temperatura:", temp, "°C")
    print("EC:", ec, "uS/cm")
    print("N:", n, "mg/kg")
    print("P:", p, "mg/kg")
    print("K:", k, "mg/kg")
    print("-----------------------")
    print("esta es nueva version")

# =========================
# BUCLE PRINCIPAL
# =========================
def main():
    ultimo_chequeo = time.time() - CHECK_INTERVAL  # chequea inmediatamente al arrancar

    while True:
        if time.time() - ultimo_chequeo >= CHECK_INTERVAL:
            check_and_update()
            ultimo_chequeo = time.time()

        leer_sensor()
        time.sleep(2)

if __name__ == "__main__":
    main()
