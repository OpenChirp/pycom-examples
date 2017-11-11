from network import LoRa
from machine import ADC
import socket
import binascii
import struct
import time
import pycom

pycom.heartbeat(False)

adc = ADC()
batt = adc.channel(attn=ADC.ATTN_11DB, pin='P16')

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
        msg = struct.pack("BH", i, int(batt.value()))
        print(msg)
        s.send(msg)
        time.sleep(60)

# get any data received...
data = s.recv(64)
print(data)
