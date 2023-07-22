# Write your code here :-)
import board
import digitalio
import time

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

chg = digitalio.DigitalInOut(board.D9)
chg.direction = digitalio.Direction.INPUT

pgood = digitalio.DigitalInOut(board.D10)
pgood.direction = digitalio.Direction.INPUT

while True:
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)
    print("CHG: {} PGOOD: {}".format(not chg.value, not pgood.value))
