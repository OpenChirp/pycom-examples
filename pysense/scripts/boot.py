# boot.py -- run on boot-up
from machine import UART
import machine
import os

uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')
