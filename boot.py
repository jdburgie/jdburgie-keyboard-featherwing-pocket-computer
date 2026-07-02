# Clear the Keyboard FeatherWing NeoPixel before code.py starts.
import time
import board
import digitalio
import neopixel_write

_pin = digitalio.DigitalInOut(board.GP10)
_pin.direction = digitalio.Direction.OUTPUT
_pin.value = False
time.sleep(0.001)
neopixel_write.neopixel_write(_pin, bytearray((0, 0, 0)))
_pin.value = False
