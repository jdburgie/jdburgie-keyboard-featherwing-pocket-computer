# Force the Keyboard FeatherWing NeoPixel OFF.
# The NeoPixel data pin is D11 / Pico GP10.
#
# This is intentionally not a test or animation. It writes one black pixel
# immediately and holds the data line low for the life of the program.

import time
import digitalio
import neopixel_write
import kfw_pico_board as board

_pin = digitalio.DigitalInOut(board.D11)
_pin.direction = digitalio.Direction.OUTPUT
_pin.value = False
time.sleep(0.001)

_black = bytearray((0, 0, 0))
neopixel_write.neopixel_write(_pin, _black)

_pin.value = False
