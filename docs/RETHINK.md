# Keyboard FeatherWing Pocket Computer: v4 Rethink

## Executive decision

Stop patching the v3 prototype in place. Preserve it as the session baseline, then rebuild the runtime around three rules:

1. Initialize shared hardware once.
2. Apps return normally to a single in-process menu.
3. Prove the SD card at the raw block level before mounting or formatting it.

The v3 branch is valuable as an experiment log, but it is not a stable base for PyDOS.

## What we learned

### The basic hardware is healthy

The Pico W, ILI9341 display, Keyboard FeatherWing I2C controller, touch controller, keyboard, Wi-Fi, and CircuitPython installation all worked during the session.

Observed I2C addresses:

- `0x1F`: keyboard controller
- `0x4B`: touch controller

### The NeoPixel is a hard requirement

The onboard NeoPixel must stay off. The production design must clear it in `boot.py`, keep the data line low, and never run an LED test or animation.

### The current launcher is too clever

The v3 launcher uses `supervisor.set_next_code_file()` and soft reloads to jump between files. That created confusing lifecycle behavior and, in practice, exiting an app could land at the REPL instead of returning to the menu.

The new design should not switch code files. A single `code.py` process owns the hardware, menu, and app lifecycle. Each app implements `run(context)` and returns when Q is pressed.

### The SD formatter was solving the wrong layer

The reported error was:

```text
OSError: timeout waiting for v2 card
```

That occurs during the SD protocol initialization handshake, before a filesystem is mounted and before formatting can begin. A formatter cannot repair a card that has not become a usable block device.

A likely contributing bug in v3 is SPI startup order. The display was initialized and sent SPI traffic before the SD chip-select pin was explicitly driven HIGH. Current CircuitPython guidance requires every chip-select line on a shared SPI bus to be in a known HIGH state before any SPI transaction. The v4 boot sequence must enforce this before constructing the display or SD driver.

### The improvised Gothic font was the wrong tradeoff

`terminalio.FONT` scales in integer steps. Its 1x size is small and 2x is large. The custom synthetic intermediate fonts consumed code, memory, and attention while producing poor legibility.

v4 will use the standard terminal font and better layout, spacing, borders, color hierarchy, and concise text. A real BDF/PCF font can be added later as an optional theme after the core is stable. No generated pseudo-Gothic font belongs in the core firmware.

## v4 architecture

```text
boot.py
  - force NeoPixel off
  - disable the display status bar
  - create D5, D6, and D9 outputs and drive all HIGH
  - do not initialize the SPI bus

code.py
  - construct HardwareContext once
  - start AppManager
  - catch app exceptions and show a recoverable error screen

src/hardware.py
  - one SPI object
  - one I2C object
  - one display object
  - one keyboard object
  - explicit cleanup methods for optional peripherals

src/ui.py
  - standard terminalio font
  - reusable title, status, body, and footer regions
  - no per-screen display reinitialization
  - no font synthesis

src/input.py
  - normalized key events
  - debounce and long-press handling in one place
  - global Q/back behavior

src/app_manager.py
  - menu loop
  - call app.run(context)
  - app returns to menu
  - exception boundary and memory cleanup

src/services/sd_service.py
  - raw SD probe
  - sector read test
  - filesystem mount
  - write verification
  - optional destructive format, only after raw probe succeeds

apps/
  - diagnostics.py
  - wifi_radar.py
  - system_info.py
  - sd_manager.py
  - later: pydos_launcher.py
```

## Boot order

The boot order is part of the hardware contract:

1. Set TFT CS `D9` HIGH.
2. Set touch CS `D6` HIGH.
3. Set SD CS `D5` HIGH.
4. Force NeoPixel data `D11` LOW and send one black pixel.
5. Disable CircuitPython's on-display status bar.
6. Create SPI.
7. Create the display.
8. Create I2C and keyboard.
9. Enter the menu.

No SPI peripheral may transmit before all chip-select pins are HIGH.

## SD-card diagnostic ladder

The SD feature should be rebuilt as a sequence of independent gates.

### Gate 1: raw initialization

- Confirm all shared SPI chip selects are HIGH.
- Construct `sdcardio.SDCard` at a conservative operating baud rate.
- Report the exact exception and elapsed time.
- Do not mention formatting if this gate fails.

### Gate 2: block access

- Call `count()`.
- Read sector 0 into a 512-byte buffer.
- Display capacity and a short boot-sector signature.
- No writes yet.

### Gate 3: filesystem mount

- Construct `storage.VfsFat`.
- Mount read-only first.
- List the root directory.

### Gate 4: write verification

- Remount writable.
- Create, read, and delete a small test file.
- Sync and unmount cleanly.

### Gate 5: formatting

Only offer Format when Gates 1 and 2 pass but Gate 3 identifies an invalid or unsupported filesystem. Formatting must remain hidden under an Advanced menu and require two confirmations.

### Failure interpretation

- No response / no card: seating, slot, CS, SPI wiring, or card failure.
- Timeout waiting for v2 card: card/contact/power/SPI initialization issue, not filesystem formatting.
- Raw block reads work but VfsFat fails: filesystem problem; formatting may help.
- Mount works but write fails: write protection, power integrity, or filesystem corruption.

## App lifecycle

Every app follows the same contract:

```python
def run(context):
    while True:
        event = context.input.next_event()
        if event.is_back:
            return
```

There is no `sys.exit()`, no `set_next_code_file()`, and no soft-reload dependency for ordinary navigation.

The app manager wraps each app call:

```python
try:
    app.run(context)
except Exception as exc:
    context.ui.show_error(exc)
finally:
    context.cleanup_optional_resources()
    gc.collect()
```

This keeps Q deterministic and prevents one app failure from dumping the user into the REPL.

## UI direction

The screen should feel like a small instrument, not a scaled desktop.

- Use 1x terminal font for body text.
- Use 2x only for very short titles when it genuinely fits.
- Prefer bordered panels, inverse selection rows, and whitespace over larger fonts.
- Keep every action visible in the footer.
- Use consistent colors: cyan title, white selection, amber warning, red destructive action, green success.
- Limit screens to one primary task.

A real Gothic font can later be an optional title-only theme loaded from a user-provided font file. It should never be required for booting or diagnostics.

## Storage and memory decision

Do not add an external memory chip.

The Pico W has enough internal flash and RAM for a reliable menu, diagnostics, Wi-Fi radar, and a modest set of utilities. The microSD card is the right place for PyDOS files, BASIC programs, logs, notes, and data after its hardware path is proven.

A Pico 2 W remains a future performance upgrade, not a prerequisite.

## PyDOS decision

Do not install PyDOS yet.

PyDOS becomes Milestone 6, after the following are repeatably stable:

1. boot and menu
2. keyboard navigation
3. app return behavior
4. SD raw initialization
5. SD mount and writes
6. repeated Wi-Fi scans without memory exhaustion

PyDOS should initially run as a separate validated package or SD-card image, not be interwoven with the core menu.

## Milestones

### M0: baseline preservation

- Tag the current v3 snapshot.
- Document observed failures.

### M1: stable shell

- Single-process menu.
- Hardware initialized once.
- NeoPixel always off.
- Q returns from every app.
- No SD or formatter code yet.

### M2: hardware diagnostics

- Display, keyboard, touch, Wi-Fi, memory.
- Shared SPI chip-select verification.

### M3: SD raw probe

- Raw init, capacity, sector read.
- Test with known-good 8 GB, 16 GB, and 32 GB cards.

### M4: SD filesystem

- Mount, list, write, delete, sync, unmount.
- Formatter only after raw tests pass.

### M5: useful applications

- Wi-Fi radar.
- Notes/log viewer.
- Sensor dashboard framework.

### M6: PyDOS

- SD-backed program library.
- Menu entry only after a clean launch/exit path is proven.

## Acceptance tests

- 20 cold boots with the menu appearing every time.
- 20 launches and Q-returns for each app.
- Run Wi-Fi scan 25 times without a crash or declining free memory.
- Boot with no SD card and receive a clear, fast error.
- Insert a known-good FAT32 card before power-on and mount it.
- Read sector 0 and report capacity before attempting VfsFat.
- Write, read, delete, sync, and unmount a test file.
- Power-cycle after SD failure and recover without reinstalling firmware.
- NeoPixel remains dark during every test.
- Any exception is displayed in-app with a return-to-menu option.

## Definition of done for v4 core

The core is complete when boot, menu navigation, Q-return, diagnostics, and raw SD probing are deterministic enough that failures point to one layer instead of producing ambiguous behavior.
