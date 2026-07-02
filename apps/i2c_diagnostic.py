# Keyboard FeatherWing I2C diagnostic app
import time
import sys
import displayio
import terminalio
import fourwire

import pixel_off
from app_control import return_to_menu  # Always force the FeatherWing NeoPixel off.

import kfw_pico_board as board
import adafruit_ili9341
from adafruit_display_text import label
from gothic_font import add_gothic_text
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_LONG_PRESS

displayio.release_displays()
display_bus = fourwire.FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
)
display = adafruit_ili9341.ILI9341(
    display_bus,
    width=320,
    height=240,
    rotation=0,
)

screen = displayio.Group()
display.root_group = screen

background = displayio.Bitmap(320, 240, 1)
palette = displayio.Palette(1)
palette[0] = 0x071018
screen.append(displayio.TileGrid(background, pixel_shader=palette))

def add(text, x, y, color=0xFFFFFF, scale=1):
    item = label.Label(
        terminalio.FONT,
        text=text,
        x=x,
        y=y,
        color=color,
        scale=scale,
    )
    screen.append(item)
    return item

add_gothic_text(screen, "I2C DIAGNOSTIC", 10, 8, 0x63F2FF)
status = add("Scanning GP4 / GP5...", 10, 56, 0xFFD166)

i2c = board.I2C()
while not i2c.try_lock():
    pass
try:
    addresses = i2c.scan()
finally:
    i2c.unlock()

found = "  ".join("0x{:02X}".format(address) for address in addresses)

if addresses:
    status.text = "FOUND: " + found
    status.color = 0x66FF99
else:
    status.text = "NO I2C DEVICES FOUND"
    status.color = 0xFF6666

if 0x1F in addresses:
    add("0x1F  KEYBOARD CONTROLLER: OK", 10, 98, 0x66FF99)
else:
    add("0x1F  KEYBOARD CONTROLLER: MISSING", 10, 98, 0xFF6666)

if 0x4B in addresses:
    add("0x4B  TOUCH CONTROLLER: OK", 10, 126, 0x66FF99)
else:
    add("0x4B  TOUCH CONTROLLER: MISSING", 10, 126, 0xFFAA66)

add("Q  RETURN TO BOOT MENU", 10, 212, 0xFFD166)

if 0x1F not in addresses:
    while True:
        time.sleep(1)

keyboard = BBQ10Keyboard(i2c)

while True:
    if keyboard.key_count:
        event = keyboard.key
        if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
            key = event[1]
            if isinstance(key, str) and key.lower() == "q":
                return_to_menu()
    time.sleep(0.015)
