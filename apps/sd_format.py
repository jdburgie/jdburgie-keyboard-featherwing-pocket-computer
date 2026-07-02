# SD CARD FORMATTER
# WARNING: Erases the entire card.

import time
import sys
import os
import displayio
import terminalio
import fourwire
import storage

import pixel_off
from app_control import return_to_menu
import kfw_pico_board as board
import adafruit_ili9341
from adafruit_display_text import label
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_LONG_PRESS
from gothic_font import add_gothic_text
from sd_support import open_card, close_card

ENTER_KEYS = ("\n", "\r")
BACKSPACE = "\x08"

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

add_gothic_text(screen, "FORMAT SD CARD", 10, 8, 0xFF6666)
line1 = label.Label(
    terminalio.FONT,
    text="THIS ERASES THE ENTIRE CARD.",
    x=10, y=48, color=0xFF6666,
)
screen.append(line1)
line2 = label.Label(
    terminalio.FONT,
    text="Files cannot be recovered here.",
    x=10, y=66, color=0xFFAA66,
)
screen.append(line2)
line3 = label.Label(
    terminalio.FONT,
    text="Type FORMAT, then press Enter.",
    x=10, y=98, color=0xFFD166,
)
screen.append(line3)

typed_label = add_gothic_text(screen, "> ", 10, 120, 0xFFFFFF)

status = label.Label(
    terminalio.FONT,
    text="Q cancels and returns to menu.",
    x=10, y=166, color=0x9DB0BA,
)
screen.append(status)
detail = label.Label(
    terminalio.FONT,
    text="",
    x=10, y=190, color=0xD6F5FF,
)
screen.append(detail)
footer = label.Label(
    terminalio.FONT,
    text="",
    x=10, y=218, color=0x9DB0BA,
)
screen.append(footer)

i2c = board.I2C()
keyboard = BBQ10Keyboard(i2c)

for _attempt in range(12):
    try:
        keyboard.backlight = 0.70
        break
    except OSError:
        time.sleep(0.2)

typed = ""

def set_typed():
    typed_label.set("> " + typed, 0xFFFFFF)

def wait_key():
    while True:
        if keyboard.key_count:
            event = keyboard.key
            if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
                return event[1]
        time.sleep(0.012)

def readable_size(byte_count):
    value = float(byte_count)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            return "{:.2f} {}".format(value, unit)
        value /= 1024.0

while True:
    key = wait_key()

    if isinstance(key, str) and key.lower() == "q" and not typed:
        return_to_menu()

    if key == BACKSPACE:
        typed = typed[:-1]
        set_typed()
        continue

    if key in ENTER_KEYS:
        if typed.upper() != "FORMAT":
            status.text = "Confirmation did not match."
            status.color = 0xFFAA66
            typed = ""
            set_typed()
            continue
        break

    if isinstance(key, str) and len(key) == 1 and key.isalpha():
        if len(typed) < 6:
            typed += key.upper()
            set_typed()

status.text = "Probing card; allow about 10 seconds..."
status.color = 0xFFD166
detail.text = ""
footer.text = ""

card = None
cs = None

try:
    card, cs = open_card()
    capacity = card.count() * 512
    detail.text = "Detected capacity: " + readable_size(capacity)
except Exception as error:
    status.text = "CARD INITIALIZATION FAILED"
    status.color = 0xFF6666
    detail.text = type(error).__name__ + ": " + str(error)[:28]
    footer.text = "Power off, reseat card, then retry. Q menu."
    while True:
        key = wait_key()
        if isinstance(key, str) and key.lower() == "q":
            close_card(cs)
            return_to_menu()

status.text = "FORMATTING... DO NOT REMOVE POWER"
status.color = 0xFF6666
line1.text = "Creating a FAT filesystem."
line1.color = 0xD6F5FF
line2.text = "This can take a little while."
line2.color = 0xD6F5FF
line3.text = ""
typed_label.set("", 0xFFFFFF)
time.sleep(0.2)

try:
    storage.VfsFat.mkfs(card)
    filesystem = storage.VfsFat(card)
    storage.mount(filesystem, "/sd")
    filesystem.label = "POCKETSD"

    for folder in ("APPS", "DATA", "GAMES", "LOGS", "NOTES", "PYDOS"):
        try:
            os.mkdir("/sd/" + folder)
        except OSError:
            pass

    with open("/sd/README.TXT", "w") as handle:
        handle.write(
            "Formatted by the Keyboard FeatherWing pocket computer.\n"
            "Volume label: POCKETSD\n"
        )

    with open("/sd/FORMAT_OK.TXT", "w") as handle:
        handle.write("SD card format and write verification passed.\n")

    with open("/sd/FORMAT_OK.TXT", "r") as handle:
        verified = "passed" in handle.read()

    status.text = "FORMAT COMPLETE"
    status.color = 0x66FF99
    line1.text = "Volume label: POCKETSD"
    line1.color = 0xD6F5FF
    line2.text = "Folders created:"
    line2.color = 0xD6F5FF
    line3.text = "APPS DATA GAMES LOGS NOTES PYDOS"
    line3.color = 0xFFFFFF
    detail.text = "Write verification: " + ("PASS" if verified else "FAIL")
    detail.color = 0x66FF99 if verified else 0xFF6666
    footer.text = "Press Q to return to boot menu."

except Exception as error:
    status.text = "FORMAT FAILED"
    status.color = 0xFF6666
    line1.text = type(error).__name__
    line2.text = str(error)[:46]
    line3.text = ""
    detail.text = "The card was not removed."
    footer.text = "Press Q to return."

while True:
    key = wait_key()
    if isinstance(key, str) and key.lower() == "q":
        close_card(cs)
        return_to_menu()
