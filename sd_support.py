# Keyboard FeatherWing microSD helper.
# Official FeatherWing mapping: SD CS = D5 / Pico GP6.

import time
import digitalio
import storage
import adafruit_sdcard

import kfw_pico_board as board


def unmount():
    try:
        storage.umount("/sd")
    except Exception:
        pass


def open_card(attempts=1):
    """Initialize the card with retries and the compatibility SPI driver."""
    unmount()
    last_error = None

    for attempt in range(attempts):
        cs = digitalio.DigitalInOut(board.D5)
        try:
            # The Adafruit driver initializes at 250 kHz with extra clocks,
            # then uses this conservative operating speed.
            card = adafruit_sdcard.SDCard(
                board.SPI(),
                cs,
                baudrate=500000,
            )
            return card, cs
        except Exception as error:
            last_error = error
            try:
                cs.deinit()
            except Exception:
                pass
            time.sleep(0.45 + attempt * 0.25)

    raise last_error


def mount_card():
    card, cs = open_card()
    filesystem = storage.VfsFat(card)
    storage.mount(filesystem, "/sd")
    return card, cs, filesystem


def close_card(cs=None):
    unmount()
    if cs is not None:
        try:
            cs.deinit()
        except Exception:
            pass
