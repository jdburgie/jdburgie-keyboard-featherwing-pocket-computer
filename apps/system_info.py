# Pico W system information app
import time
import sys
import gc
import microcontroller
import wifi
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

def add(text, y, color=0xD6F5FF, scale=1):
    item = label.Label(
        terminalio.FONT,
        text=text,
        x=10,
        y=y,
        color=color,
        scale=scale,
    )
    screen.append(item)

gc.collect()
mac = ":".join("{:02X}".format(byte) for byte in wifi.radio.mac_address)

add_gothic_text(screen, "SYSTEM INFO", 10, 8, 0x63F2FF)
add("Board: " + board.board_id, 58)
add("CPU: {} MHz".format(microcontroller.cpu.frequency // 1000000), 82)
add("Free RAM: {} bytes".format(gc.mem_free()), 106)
add("Wi-Fi MAC:", 130)
add(mac, 150, 0xFFFFFF)
add("CircuitPython boot menu active", 180, 0x66FF99)
add("Q  RETURN TO BOOT MENU", 216, 0xFFD166)

i2c = board.I2C()
keyboard = BBQ10Keyboard(i2c)

while True:
    if keyboard.key_count:
        event = keyboard.key
        if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
            key = event[1]
            if isinstance(key, str) and key.lower() == "q":
                return_to_menu()
    time.sleep(0.015)
