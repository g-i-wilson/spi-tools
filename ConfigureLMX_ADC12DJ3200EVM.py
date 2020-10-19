import time
import sys
from pyftdi.spi import SpiController
from pyftdi.gpio import GpioSyncController
import FTDISPI
import JSONFile


SCLK = 0x01
MOSI = 0x02
MISO = 0x10
CS = 0x08

gpio = GpioSyncController()
# lmxAdc = SpiController()
gpio.configure('ftdi:///3', direction=(SCLK|MOSI|CS), frequency=1e3)
# lmxAdc.configure('ftdi:///2')

lmx = FTDISPI.Interface( \
    FTDISPI.GPIO(
        gpio, \
        SCLK = SCLK, \
        MOSI = MOSI, \
        MISO = MISO, \
        CS = CS, \
    ), \
    defaultMap  = "LMX2582.json", \
    currentState = "LMX2582_current_state.json", \
    previousState = "LMX2582_previous_state.json",
)


# lmx.writeCSV(sys.argv[1])
# print("*** LMK ***")
# lmx.readState()

FTDISPI.uiLoop(lmx)
