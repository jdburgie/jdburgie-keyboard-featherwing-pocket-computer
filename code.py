# POCKET COMPUTER BOOT MENU
# Raspberry Pi Pico W + Solder Party Keyboard FeatherWing Rev. 2

import time
import displayio
import terminalio
import fourwire
import supervisor

import pixel_off
import kfw_pico_board as board
import adafruit_ili9341
from adafruit_display_text import label
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_LONG_PRESS
from gothic_font import add_gothic_text

UP = "\x01"
DOWN = "\x02"
RIGHT = "\x04"
ENTER_KEYS = ("\n", "\r")

APPS = (
    ("SD CARD", "/apps/sd_card.py", "Mount, test, and browse microSD"),
    ("FORMAT SD", "/apps/sd_format.py", "ERASE and format the microSD card"),
    ("WI-FI RADAR", "/apps/wifi_radar.py", "Nearby access-point scanner"),
    ("I2C TEST", "/apps/i2c_diagnostic.py", "Keyboard and touch check"),
    ("SYSTEM INFO", "/apps/system_info.py", "Pico W status and memory"),
)

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

root = displayio.Group()
display.root_group = root

background = displayio.Bitmap(320, 240, 1)
palette = displayio.Palette(1)
palette[0] = 0x050A12
root.append(displayio.TileGrid(background, pixel_shader=palette))

add_gothic_text(root, "POCKET COMPUTER", 12, 8, 0x63F2FF)
add_gothic_text(root, "BOOT MENU", 12, 25, 0xFFD166)

menu_rows = []
for index in range(len(APPS)):
    menu_item = add_gothic_text(
        root,
        "",
        18,
        52 + index * 26,
        0x65C8D0,
    )
    menu_rows.append(menu_item)

description = label.Label(
    terminalio.FONT,
    text="",
    x=12,
    y=211,
    color=0x9DB0BA,
)
root.append(description)

footer = label.Label(
    terminalio.FONT,
    text="UP/DOWN SELECT   ENTER/RIGHT LAUNCH",
    x=12,
    y=230,
    color=0x9DB0BA,
)
root.append(footer)

i2c = board.I2C()

def scan_i2c():
    while not i2c.try_lock():
        time.sleep(0.01)
    try:
        return i2c.scan()
    finally:
        i2c.unlock()

description.text = "Waiting for keyboard controller..."
deadline = time.monotonic() + 8

while 0x1F not in scan_i2c():
    if time.monotonic() >= deadline:
        description.text = "Keyboard 0x1F not found. Reseat adapter."
        while True:
            time.sleep(1)
    time.sleep(0.2)

keyboard = BBQ10Keyboard(i2c)

for _attempt in range(12):
    try:
        keyboard.backlight = 0.70
        break
    except OSError:
        time.sleep(0.2)

selected = 0

def draw_menu():
    for index, app in enumerate(APPS):
        marker = ">" if index == selected else " "
        menu_rows[index].set(
            "{} {}".format(marker, app[0]),
            0xFFFFFF if index == selected else 0x65C8D0,
        )
    description.text = APPS[selected][2]

def launch(path):
    description.text = "Launching {}...".format(APPS[selected][0])
    time.sleep(0.15)
    supervisor.set_next_code_file(
        path,
        reload_on_success=True,
        reload_on_error=True,
        sticky_on_success=False,
        sticky_on_error=False,
        sticky_on_reload=True,
    )
    supervisor.reload()

draw_menu()

while True:
    if keyboard.key_count:
        event = keyboard.key
        if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
            key = event[1]

            if key == UP:
                selected = (selected - 1) % len(APPS)
                draw_menu()
            elif key == DOWN:
                selected = (selected + 1) % len(APPS)
                draw_menu()
            elif key == RIGHT or key in ENTER_KEYS:
                launch(APPS[selected][1])
            elif isinstance(key, str):
                shortcut = key.lower()
                if shortcut == "d":
                    selected = 0
                    launch(APPS[selected][1])
                elif shortcut == "f":
                    selected = 1
                    launch(APPS[selected][1])
                elif shortcut == "w":
                    selected = 2
                    launch(APPS[selected][1])
                elif shortcut == "i":
                    selected = 3
                    launch(APPS[selected][1])
                elif shortcut == "s":
                    selected = 4
                    launch(APPS[selected][1])

    time.sleep(0.012)
