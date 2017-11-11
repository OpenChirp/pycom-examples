from pysense import Pysense
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE
from network import LoRa
import socket
import binascii
import struct
import time
import pycom

py = Pysense()
mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
#mp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
si = SI7006A20(py)
lt = LTR329ALS01(py)
li = LIS2HH12(py)

# Initialize LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN, adr=True, public=True, tx_retries=0)

# create an OTAA authentication parameters
app_eui = binascii.unhexlify('<Insert your app eui here!>'.replace(' ',''))
app_key = binascii.unhexlify('<Insert your app key here!>'.replace(' ',''))

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    # join a network using ABP (Activation By Personalization)
    time.sleep(1)
    print("retrying...")
print("Joined LoRa Network!")

# Print LoRa Stats
lora.stats()

# Call back for T/RX Messages
def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        print('Lora packet received')
    if events & LoRa.TX_PACKET_EVENT:
        print('Lora packet sent')

lora.callback(trigger=(LoRa.RX_PACKET_EVENT | LoRa.TX_PACKET_EVENT), handler=lora_cb)

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
#s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# selecting confirmed type of messages
s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

# make the socket non-blocking
s.setblocking(False)

# send some data
while True:
    for i in range(0, 0xff):
        light = lt.light()
        msg = struct.pack("ffffiifff", mp.temperature(), mp.altitude(), si.temperature(), si.humidity(), light[0], light[1], li.roll(), li.pitch(), py.read_battery_voltage())
        #msg = struct.pack("ffffiifff", mp.temperature(), mp.pressure(), si.temperature(), si.humidity(), light[0], light[1], li.roll(), li.pitch(), py.read_battery_voltage())
        print(msg)
        s.send(msg)
        time.sleep(60)

# get any data received...
data = s.recv(64)
print(data)
