"""
  Telegram Bot using CircuitPython on Raspberry Pi Pico W

  Items:
  - Maker Pi Pico Mini
    https://my.cytron.io/p-maker-pi-pico-mini-simplifying-projects-with-raspberry-pi-pico
  - USB Micro B Cable
    https://my.cytron.io/p-usb-micro-b-cable

  CircuitPython Raspberry Pi Pico W
  https://circuitpython.org/board/raspberry_pi_pico_w/
  - Tested with CircuitPython 8.0.0-beta.2

  CircuitPython Additional libraries
  https://circuitpython.org/libraries
  - adafruit_requests.mpy
  - simpleio.mpy
"""
import os
import sys
import time
import microcontroller
import board
import digitalio
import simpleio
import wifi
import socketpool
import adafruit_requests
import ssl
import busio
import adafruit_htu31d
from adafruit_bme280 import basic as adafruit_bme280
import math
import sdcardio
import storage
import adafruit_sdcard



# HTU31D
i2c = busio.I2C(board.GP5, board.GP4)  # Pi Pico RP2040 (scl, sda)
htu = adafruit_htu31d.HTU31D(i2c)

# BMX
bme280_i2c = busio.I2C(board.GP7, board.GP6)  # scl, sca
bme280 = adafruit_bme280.Adafruit_BME280_I2C(bme280_i2c)


# bme280.sea_level_pressure = 1013.4 #presion nivel del mar


# datos_clima = "Datos actuales \nTemperatura:  %0.1f Grados \nHumedad:  %0.1f  \nPresion: %0.1f hPa" %(temperatura,humedad,presion)
# datos_clima= "Humedad: %0.1f %%" % humedad," Temperatura: %0.1f Grados" % temperatura," Presion: %0.1f hPa" % presion
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("All secret keys are kept in secrets.py, please add them there!")
    raise
# Telegram API url.
API_URL = "https://api.telegram.org/bot" + secrets["telegram_bot_token"]

NOTE_G4 = 392
NOTE_C5 = 523
buzzer = board.GP18


led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

#log



# punto rocio
b = 17.62
c = 243.12

# temp_minmax
t_min = 1000
t_max = -1000


def init_bot():
    get_url = API_URL
    get_url += "/getMe"
    r = requests.get(get_url)
    return r.json()["ok"]


first_read = True
update_id = 0


def read_message():
    global first_read
    global update_id

    get_url = API_URL
    get_url += '/getUpdates?limit=1&allowed_updates=["message","callback_query"]'
    if first_read == False:
        get_url += "&offset={}".format(update_id)
    r = requests.get(get_url)
    # print(r.json())

    try:
        update_id = r.json()["result"][0]["update_id"]
        message = r.json()["result"][0]["message"]["text"]
        message = message.lower()
        chat_id = r.json()["result"][0]["message"]["chat"]["id"]

        # print("Update ID: {}".format(update_id))
        print("Chat ID: {}\tMessage: {}".format(chat_id, message))

        first_read = False
        update_id += 1
        simpleio.tone(buzzer, NOTE_G4, duration=0.1)
        simpleio.tone(buzzer, NOTE_C5, duration=0.1)

        return chat_id, message
    except (IndexError) as e:
        # print("No new message")
        return False, False


def send_message_original(chat_id, message):
    get_url = API_URL
    get_url += "/sendMessage?chat_id={}&text={}".format(chat_id, message)
    r = requests.get(get_url)
    # print(r.json())


def send_message(chat_id, message):
    get_url = API_URL
    get_url += "/sendMessage?chat_id={}&text={}".format(chat_id, message)
    try:
        r = requests.get(get_url)
    except Exception as e:
        print("DEBUG error de envio\n", e)
        print("DEBUG message: ", message)
        print("DEBUG get_url: ", get_url)


def send_message_privado(chat_id, message):
    get_url = API_URL
    get_url += "/sendMessage?chat_id={}&text={}".format(chat_id, message)
    encode_url = get_url.encode("UTF-8")
    try:
        r = requests.post(encode_url)
    except Exception as e:
        print("DEBUG error de envio tipo POST\n", e)
        print("DEBUG message: ", message)
        print("DEBUG get_url: ", get_url)


def borrar_mensajes_viejos():
    try:
        chat_id = True
        message_in = True
        while chat_id != False and message_in != False:
            chat_id, message_in = read_message()
        print("Mensajes viejos borrados")
    except:
        print("Error borrando mensajes viejos")


print(f"Initializing...")


while not wifi.radio.ipv4_address or "0.0.0.0" in repr(wifi.radio.ipv4_address):
    print(f"Connecting to WiFi...")
    wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
print("IP Address: {}".format(wifi.radio.ipv4_address))

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

if init_bot() == False:
    print("Telegram bot failed.")

else:
    print("Telegram bot ready!\n")

    simpleio.tone(buzzer, NOTE_C5, duration=0.1)

    borrar_mensajes_viejos()

    while True:
        try:
            while not wifi.radio.ipv4_address or "0.0.0.0" in repr(
                wifi.radio.ipv4_address
            ):
                print(f"Reconnecting to WiFi...")
                wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])

            chat_id, message_in = read_message()

            if message_in == "/start":
                send_message(
                    chat_id,
                    "Bienvendos a la version alfa del PyMeteo_Sorbas. Pida /ayuda para saber los comandos",
                )
            elif message_in == "/ayuda":
                send_message(chat_id, "Comandos: ")
                send_message(chat_id, "/led_on " + ".Enciende led")
                send_message(chat_id, "/led_off " + ".Apaga led")
                send_message(chat_id, "/temperatura " + ".Muestra temperatura")
                send_message(chat_id, "/humedad " + ".Muestra humedad relativa")
                send_message(
                    chat_id,
                    "/clima "
                    + ".Muestra los datos de la temperatura, humedad, presion relativa y punto de rocio",
                )
                send_message(
                    chat_id,
                    "/presion " + ". Muestra la presion absoluta y la presion relativa",
                )
                send_message(chat_id, "/ayuda " + ".Muestra los comandos")
                send_message(chat_id, "/min " + ". Muestra la temperatura minima ")
                send_message(chat_id, "/max " + ". Muestra la temperatura maxima")
                send_message(
                    chat_id, "/minmax" + ". Muestra las temperaturas minima y maxima"
                )

            elif message_in == "led_on":
                led.value = True
                send_message(chat_id, "LED turn on.")

            elif message_in == "led_off":
                led.value = False
                send_message(chat_id, "LED turn off.")

            elif message_in == "/temperatura":
                led.value = False
                send_message(chat_id, "Temperatura: %0.1f C" % htu.temperature)

            elif message_in == "/humedad":
                led.value = False
                send_message(chat_id, "Humedad: %0.1f %%" % htu.relative_humidity)

            elif message_in == "/clima2":
                temperatura = htu.temperature
                humedad = htu.relative_humidity
                presion = bme280.pressure
                datos_clima2 = (
                    "Datos actuales \nTemperatura:  %0.1f ºC \nHumedad:  %0.1f  \nPresion: %0.1f hPa"
                    % (temperatura, humedad, presion)
                )
                print("datos_clima2: ", datos_clima2)
                send_message_privado(chat_id, datos_clima2)

            elif message_in == "/clima":
                temperatura = htu.temperature
                humedad = htu.relative_humidity
                presion = bme280.pressure
                altitud = bme280.altitude
                altitud = 409
                presion_relativa = presion / 0.95267905098876
                gamma = gamma = (b * temperatura / (c + temperatura)) + math.log(
                    humedad / 100.0
                )
                punto_rocio = (c * gamma) / (b - gamma)
                send_message(chat_id, "Datos actuales: ")
                send_message(chat_id, "1-Temperatura:  %0.1f grados " % temperatura)
                send_message(chat_id, "2-Humedad relativa :  %0.1f %% " % humedad)
                send_message(
                    chat_id, "3-Presion relativa : %0.1f hPa " % presion_relativa
                )
                send_message(chat_id, "4-punto de rocio : %0.1f grados " % punto_rocio)

            elif message_in == "/presion":
                led.value = False
                send_message(chat_id, "Presion absoluta : %0.1f hPa" % bme280.pressure)
                send_message(chat_id, "Presion relativa:  %0.1f hPa" % presion_relativa)

            elif message_in == "/min":
                t_actual = htu.temperature
                if t_actual < t_min:
                    t_min = t_actual
                    send_message(chat_id, t_min)

            elif message_in == "/max":
                t_actual = htu.temperature
                if t_actual > t_max:
                    t_max = t_actual
                    send_message(chat_id, t_max)

            elif message_in == "/minmax":
                t_actual = htu.temperature
                if t_actual < t_min:
                    t_min = t_actual
                if t_actual > t_max:
                    t_max = t_actual
                send_message(chat_id, "temperatura minima: %0.1f grados " % t_min)
                send_message(chat_id, "temperatura maxima: %0.1f grados " % t_max)

            else:
                send_message(chat_id, "Para todo lo demas, MasterCard")
        except OSError as e:
            print("Failed!\n", e)
            microcontroller.reset()
