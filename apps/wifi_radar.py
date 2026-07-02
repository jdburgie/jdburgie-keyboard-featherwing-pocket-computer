# Pocket Wi-Fi Radar
# Raspberry Pi Pico W + Solder Party Keyboard FeatherWing Rev. 2
# CircuitPython 10.x

import time
import sys
import displayio
import terminalio
import wifi
import fourwire

import pixel_off
from app_control import return_to_menu  # Always force the FeatherWing NeoPixel off.

import kfw_pico_board as board
import adafruit_ili9341
from adafruit_display_text import label
from gothic_font import add_gothic_text
from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_LONG_PRESS

WIDTH = 320
HEIGHT = 240
VISIBLE_ROWS = 10

displayio.release_displays()
spi = board.SPI()
display_bus = fourwire.FourWire(
    spi,
    command=board.D10,
    chip_select=board.D9,
)
display = adafruit_ili9341.ILI9341(
    display_bus,
    width=WIDTH,
    height=HEIGHT,
    rotation=0,
)

root_group = displayio.Group()
display.root_group = root_group

background_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0x071018
root_group.append(displayio.TileGrid(background_bitmap, pixel_shader=background_palette))

title = add_gothic_text(
    root_group,
    "POCKET WI-FI RADAR",
    8,
    6,
    0x63F2FF,
)

status = label.Label(
    terminalio.FONT,
    text="Starting...",
    color=0xFFD166,
    x=8,
    y=34,
)
root_group.append(status)

rows = []
for index in range(VISIBLE_ROWS):
    row = label.Label(
        terminalio.FONT,
        text="",
        color=0xD6F5FF,
        x=8,
        y=54 + index * 16,
    )
    rows.append(row)
    root_group.append(row)

footer = label.Label(
    terminalio.FONT,
    text="UP/DN select RIGHT details R scan Q menu",
    color=0x9DB0BA,
    x=8,
    y=229,
)
root_group.append(footer)

i2c = board.I2C()

def scan_i2c():
    while not i2c.try_lock():
        time.sleep(0.01)
    try:
        return i2c.scan()
    finally:
        i2c.unlock()

status.text = "Waiting for keyboard controller..."
deadline = time.monotonic() + 8

while 0x1F not in scan_i2c():
    if time.monotonic() >= deadline:
        status.text = "Keyboard 0x1F not found"
        rows[0].text = "Unplug USB and reseat the adapter."
        rows[1].text = "Then reconnect power."
        while True:
            time.sleep(1)
    time.sleep(0.20)

keyboard = BBQ10Keyboard(i2c)

for attempt in range(10):
    try:
        keyboard.backlight = 0.65
        break
    except OSError:
        time.sleep(0.20)
else:
    status.text = "Keyboard found, but not responding"
    rows[0].text = "Press Ctrl-D or reconnect USB."
    while True:
        time.sleep(1)

networks = []
selected = 0
top = 0
detail_mode = False

def security_name(authmodes):
    try:
        if wifi.AuthMode.OPEN in authmodes:
            return "OPEN"
        if wifi.AuthMode.WPA3 in authmodes:
            return "WPA3"
        if wifi.AuthMode.WPA2 in authmodes:
            return "WPA2"
        if wifi.AuthMode.WPA in authmodes:
            return "WPA"
        if wifi.AuthMode.WEP in authmodes:
            return "WEP"
    except Exception:
        pass
    return "LOCK"

def bssid_text(raw):
    return ":".join("{:02X}".format(byte) for byte in raw)

def signal_meter(rssi):
    filled = int((rssi + 90) / 10)
    filled = max(0, min(5, filled))
    return "#" * filled + "." * (5 - filled)

def draw_list():
    global top
    if not networks:
        for index, row in enumerate(rows):
            row.text = "No networks found" if index == 0 else ""
        footer.text = "R rescan   Q menu"
        return

    if selected < top:
        top = selected
    if selected >= top + VISIBLE_ROWS:
        top = selected - VISIBLE_ROWS + 1

    for row_index, row in enumerate(rows):
        network_index = top + row_index
        if network_index >= len(networks):
            row.text = ""
            continue

        ap = networks[network_index]
        pointer = ">" if network_index == selected else " "
        ssid = ap["ssid"][:21]
        row.text = "{}{:<21} {:>4} {}".format(
            pointer,
            ssid,
            ap["rssi"],
            signal_meter(ap["rssi"]),
        )
        row.color = 0xFFFFFF if network_index == selected else 0xA7D8E8

    footer.text = "UP/DN select RIGHT details R scan Q menu"

def draw_details():
    ap = networks[selected]
    for row in rows:
        row.text = ""

    rows[0].text = "SSID: " + ap["ssid"][:43]
    rows[1].text = "Signal: {} dBm  [{}]".format(ap["rssi"], signal_meter(ap["rssi"]))
    rows[2].text = "Channel: {}".format(ap["channel"])
    rows[3].text = "Security: {}".format(security_name(ap["authmode"]))
    rows[4].text = "Country: {}".format(ap["country"])
    rows[5].text = "BSSID:"
    rows[6].text = bssid_text(ap["bssid"])
    rows[8].text = "Passive scanning only."
    rows[9].text = "No passwords are captured."

    for row in rows:
        row.color = 0xD6F5FF

    status.text = "Network {}/{}".format(selected + 1, len(networks))
    footer.text = "LEFT back  UP/DN change  R scan  Q menu"

def scan_networks():
    global networks, selected, top, detail_mode

    detail_mode = False
    selected = 0
    top = 0
    status.text = "Scanning the 2.4 GHz airwaves..."
    for row in rows:
        row.text = ""
    time.sleep(0.05)

    found = []
    scanner = wifi.radio.start_scanning_networks()
    try:
        for ap in scanner:
            found.append(
                {
                    "ssid": ap.ssid if ap.ssid else "<hidden>",
                    "rssi": int(ap.rssi),
                    "channel": int(ap.channel),
                    "bssid": bytes(ap.bssid),
                    "authmode": tuple(ap.authmode),
                    "country": ap.country if ap.country else "--",
                }
            )
    finally:
        wifi.radio.stop_scanning_networks()

    found.sort(key=lambda item: item["rssi"], reverse=True)
    networks = found
    status.text = "{} access points found".format(len(networks))
    draw_list()

def move_selection(change):
    global selected
    if not networks:
        return
    selected = (selected + change) % len(networks)
    if detail_mode:
        draw_details()
    else:
        draw_list()

scan_networks()

while True:
    if keyboard.key_count:
        state, key = keyboard.key

        if state in (STATE_PRESS, STATE_LONG_PRESS):
            if key == "\x01":
                move_selection(-1)
            elif key == "\x02":
                move_selection(1)
            elif key == "\x03":
                detail_mode = False
                status.text = "{} access points found".format(len(networks))
                draw_list()
            elif key == "\x04":
                if networks:
                    detail_mode = True
                    draw_details()
            elif isinstance(key, str) and key.lower() == "r":
                scan_networks()
            elif isinstance(key, str) and key.lower() == "q":
                status.text = "Returning to boot menu..."
                time.sleep(0.25)
                return_to_menu()

    time.sleep(0.015)
