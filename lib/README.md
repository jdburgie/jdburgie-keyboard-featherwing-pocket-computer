# CircuitPython libraries

Copy the required CircuitPython 10.x libraries into `CIRCUITPY/lib` before running the prototype:

- `adafruit_ili9341.mpy`
- `adafruit_display_text/`
- `adafruit_bus_device/`
- `bbq10keyboard.mpy`
- `adafruit_sdcard.mpy` or `adafruit_sdcard.py`

The historical local checkpoint included a vendored copy of `adafruit_sdcard.py`. This GitHub repository intentionally records it as an external MIT-licensed dependency instead of duplicating the upstream library.
