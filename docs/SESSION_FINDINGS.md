# Session findings

## Confirmed working

- Raspberry Pi Pico W with CircuitPython 10.2.1
- ILI9341 320x240 display
- Keyboard controller at I2C address 0x1F
- Touch controller at I2C address 0x4B
- Keyboard input and backlight control
- Wi-Fi access-point scanning
- Boot menu rendering
- NeoPixel shutdown

## Important observations

### Keyboard startup timing

The keyboard controller may not be ready for an immediate register write. Waiting until address 0x1F appears on the I2C bus resolved the startup problem.

### CircuitPython compatibility

CircuitPython does not implement every CPython API. The Star Trek prototype had to replace weighted `random.choices()` with an explicit weighted roll.

### Application lifecycle

The multi-file launcher sometimes finished an app at the CircuitPython console instead of returning to the menu. The redesign should keep one process alive and have apps return normally.

### SD card

Both attempted SD drivers stopped during card initialization, before mounting or formatting. The v3 code also initialized the shared-SPI display before explicitly setting the SD and touch chip-select pins HIGH. The redesign must establish every shared-bus chip-select state before the first SPI transaction.

### Typography

The standard 1x terminal font was small, the 2x version was too large, and both synthetic intermediate fonts reduced readability. The redesign should use the standard font with stronger layout, spacing, panels, and selection treatment.
