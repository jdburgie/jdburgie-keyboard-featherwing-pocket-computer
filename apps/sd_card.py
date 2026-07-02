# SD CARD TEST + ROOT BROWSER

import time
import sys
import os
import displayio
import terminalio
import fourwire

import pixel_off
from app_control import return_to_menu
import kfw_pico_board as board
import adafruit_ili9341
from adafruit_display_text import label
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_LONG_PRESS
from gothic_font import add_gothic_text
from sd_support import mount_card, close_card

UP = "\x01"
DOWN = "\x02"

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

add_gothic_text(screen, "SD CARD", 10, 8, 0x63F2FF)

status = label.Label(
    terminalio.FONT,
    text="Starting...",
    x=10,
    y=42,
    color=0xFFD166,
)
screen.append(status)

rows = []
for index in range(10):
    row = label.Label(
        terminalio.FONT,
        text="",
        x=10,
        y=64 + index * 14,
        color=0xD6F5FF,
    )
    rows.append(row)
    screen.append(row)

footer = label.Label(
    terminalio.FONT,
    text="Q MENU",
    x=10,
    y=226,
    color=0x9DB0BA,
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


def wait_for_q():
    while True:
        if keyboard.key_count:
            event = keyboard.key
            if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
                key = event[1]
                if isinstance(key, str) and key.lower() == "q":
                    return_to_menu()
        time.sleep(0.015)


def format_bytes(value):
    units = ("B", "KB", "MB", "GB")
    number = float(value)
    for unit in units:
        if number < 1024.0 or unit == units[-1]:
            return "{:.2f} {}".format(number, unit)
        number /= 1024.0


def test_write():
    test_path = "/sd/PICO_TEST.TXT"
    content = "Keyboard FeatherWing SD card test passed.\n"
    with open(test_path, "w") as handle:
        handle.write(content)
    with open(test_path, "r") as handle:
        return handle.read() == content


def list_directory(path):
    names = []
    try:
        for name in os.listdir(path):
            full_path = path + "/" + name if path != "/sd" else "/sd/" + name
            try:
                mode = os.stat(full_path)[0]
                is_dir = (mode & 0x4000) != 0
            except Exception:
                is_dir = False
            names.append(("[DIR] " if is_dir else "      ") + name)
    except Exception:
        return []
    names.sort()
    return names


status.text = "Probing card; allow about 10 seconds..."
card = None
cs = None

try:
    card, cs, filesystem = mount_card()
except Exception as error:
    status.text = "SD CARD INITIALIZATION FAILED"
    status.color = 0xFF6666
    rows[0].text = type(error).__name__
    rows[1].text = str(error)[:46]
    rows[3].text = "Power off, remove, and reinsert card."
    rows[4].text = "Then power on and retry SD CARD."
    rows[6].text = "Q returns directly to boot menu."
    wait_for_q()

write_ok = False
try:
    write_ok = test_write()
except Exception:
    write_ok = False

capacity = card.count() * 512
try:
    info = os.statvfs("/sd")
    free = info[0] * info[3]
except Exception:
    free = None

entries = list_directory("/sd")

status.text = "MOUNTED  WRITE TEST: {}".format("PASS" if write_ok else "FAIL")
status.color = 0x66FF99 if write_ok else 0xFFAA66

rows[0].text = "CAPACITY: " + format_bytes(capacity)
if free is not None:
    rows[1].text = "FREE:     " + format_bytes(free)
rows[2].text = "ROOT DIRECTORY:"

footer.text = "UP/DOWN SCROLL   R RETEST   Q MENU"
top = 0
selected = 0


def draw_entries():
    for index in range(3, 10):
        rows[index].text = ""

    if not entries:
        rows[3].text = "(no files)"
        return

    for row_index in range(7):
        entry_index = top + row_index
        if entry_index >= len(entries):
            break
        marker = ">" if entry_index == selected else " "
        rows[3 + row_index].text = marker + entries[entry_index][:43]
        rows[3 + row_index].color = (
            0xFFFFFF if entry_index == selected else 0xD6F5FF
        )


draw_entries()

while True:
    if keyboard.key_count:
        event = keyboard.key
        if event and event[0] in (STATE_PRESS, STATE_LONG_PRESS):
            key = event[1]

            if key == UP and entries:
                selected = (selected - 1) % len(entries)
                if selected < top:
                    top = selected
                elif selected == len(entries) - 1:
                    top = max(0, len(entries) - 7)
                draw_entries()

            elif key == DOWN and entries:
                selected = (selected + 1) % len(entries)
                if selected >= top + 7:
                    top = selected - 6
                elif selected == 0:
                    top = 0
                draw_entries()

            elif isinstance(key, str) and key.lower() == "r":
                status.text = "Retesting write access..."
                try:
                    write_ok = test_write()
                    status.text = "MOUNTED  WRITE TEST: {}".format(
                        "PASS" if write_ok else "FAIL"
                    )
                    status.color = 0x66FF99 if write_ok else 0xFFAA66
                except Exception as error:
                    status.text = "WRITE TEST FAILED: " + str(error)[:22]
                    status.color = 0xFF6666

            elif isinstance(key, str) and key.lower() == "q":
                close_card(cs)
                return_to_menu()

    time.sleep(0.015)
