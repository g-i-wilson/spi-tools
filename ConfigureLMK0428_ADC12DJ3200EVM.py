import time
import sys
from pyftdi.spi import SpiController
from pyftdi.gpio import GpioSyncController
import FTDISPI
import JSONFile


SCLK = 0x01
MOSI = 0x02
MISO = 0x20
CS = 0x04

lmkAdc = GpioSyncController()
# lmkAdc = SpiController()
lmkAdc.configure('ftdi:///3', direction=(SCLK|MOSI|CS), frequency=1e3)
# lmkAdc.configure('ftdi:///2')

lmk = FTDISPI.Interface( \
    FTDISPI.GPIO(
        lmkAdc, \
        SCLK = SCLK, \
        MOSI = MOSI, \
        MISO = MISO, \
        CS = CS, \
    ), \
    defaultMap  = "LMK04828.json", \
    currentState = "LMK_current_state.json", \
    previousState = "LMK_previous_state.json",
)


FTDISPI.uiLoop(lmk)
