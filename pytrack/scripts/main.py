import machine
import math
import network
import os
import time
import utime
from machine import RTC
from machine import SD
from machine import Timer
from L76GNSS import L76GNSS
from LIS2HH12 import LIS2HH12
from pytrack import Pytrack
from network import WLAN
from network import LoRa
import socket
import binascii
import struct

# setup as a station

import gc

# setup WLAN for network time!
wlan = WLAN(mode=WLAN.STA)

nets = wlan.scan()
for net in nets:
    if net.ssid == '<Insert your WiFi SSID here!>':
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, '<Insert your WiFi password here!>'), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print('WLAN connection succeeded!')
        break

# pytrack stuff
time.sleep(2)
gc.enable()

# setup rtc
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
utime.sleep_ms(750)
print('\nRTC Set from NTP to UTC:', rtc.now())
utime.timezone(7200)
print('Adjusted from UTC to EST timezone', utime.localtime(), '\n')

if wlan.isconnected():
    wlan.disconnect()
    print('WLAN disconnecting!')

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

gc.collect()

py = Pytrack()
acc = LIS2HH12()
l76 = L76GNSS(py, timeout=60)
chrono = Timer.Chrono()
chrono.start()
#sd = SD()
#os.mount(sd, '/sd')
#f = open('/sd/gps-record.txt', 'w')
while (True):

    coord = l76.coordinates()

    if coord == (None, None):
        latitude = 0
        longtitude = 0
        #print("No fix!")
    else:
        latitude = float(coord[0])
        longtitude = float(coord[1])
        #f.write("{} - {}\n".format(coord, rtc.now()))
    #print("{} - {} - {}".format(coord, rtc.now(), gc.mem_free()))

    pitch = acc.pitch()
    roll = acc.roll()
    #print('{},{}'.format(pitch,roll))

    battery = py.read_battery_voltage()
    s.send(struct.pack("fffff", pitch, roll, latitude, longtitude, battery))
    gc.collect()
