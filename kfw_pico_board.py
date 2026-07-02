# Keyboard FeatherWing pin compatibility layer for Raspberry Pi Pico boards.
import board as pico_board
import busio

_SPI = None
_UART = None
_I2C = None

A0 = pico_board.GP26
A1 = pico_board.GP27
A2 = pico_board.GP20
A3 = pico_board.GP21
A4 = pico_board.GP22
A5 = pico_board.GP28

SCK = pico_board.GP18
COPI = pico_board.GP19
MOSI = pico_board.GP19
CIPO = pico_board.GP16
MISO = pico_board.GP16

RX = pico_board.GP1
TX = pico_board.GP0

D14 = pico_board.GP13
MISC = pico_board.GP13
SCL = pico_board.GP5
SDA = pico_board.GP4
D5 = pico_board.GP6
D6 = pico_board.GP7
D9 = pico_board.GP8
D10 = pico_board.GP9
D11 = pico_board.GP10
D12 = pico_board.GP11
D13 = pico_board.GP12

LED = pico_board.LED
NEOPIXEL = D11
board_id = pico_board.board_id
kfw = True

def SPI():
    global _SPI
    if _SPI is None:
        _SPI = busio.SPI(SCK, COPI, CIPO)
    return _SPI

def UART():
    global _UART
    if _UART is None:
        _UART = busio.UART(TX, RX)
    return _UART

def I2C():
    global _I2C
    if _I2C is None:
        _I2C = busio.I2C(SCL, SDA)
    return _I2C
