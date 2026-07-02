KEYBOARD FEATHERWING V3
GOTHIC UI + RELIABLE MENU RETURN
================================

Changes:

1. Smaller Gothic-inspired font
   - New custom 8x11-pixel uppercase display font.
   - It is smaller than the previous 10x14 font.
   - It remains larger than CircuitPython's normal 6x8 terminal text.
   - Used for headings and boot-menu choices.

2. Q always returns to the boot menu
   - Apps no longer rely on sys.exit().
   - Q explicitly resets CircuitPython to the normal /code.py sequence
     and performs a supervisor reload.

3. SD-card screen no longer appears frozen for several retries
   - One initialization attempt is made.
   - The screen warns that probing can take about 10 seconds.
   - The compatibility driver remains at a conservative SPI speed.

4. NeoPixel
   - Still forcibly OFF.
   - No light test, flash, or animation is included.

INSTALL
-------

Copy everything inside this ZIP to the root of CIRCUITPY.
Replace existing files when prompted.
Keep any other libraries already present in your lib folder.

TRY SD CARD FIRST
-----------------

Choose SD CARD before FORMAT SD.

If card initialization fails:
1. Power the FeatherWing completely off.
2. Remove and firmly reinsert the microSD card.
3. Power it on again.
4. Retry SD CARD.

Q should now return directly to the boot menu from every application.
