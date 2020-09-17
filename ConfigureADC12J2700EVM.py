import time
import sys
from pyftdi.spi import SpiController
from pyftdi.gpio import GpioSyncController
import FTDISPI


# spiAdc = SpiController()
# spiAdc.configure('ftdi:///1')
# slaveAdc = spiAdc.get_port( \
#     cs=0, \
#     freq=1e6, \
#     mode=0 \
# )
# adc = FTDISPI.Interface( \
#     FTDISPI.MPSSE(slaveAdc), \
#     defaultMap  = "ADC12J2700.json", \
#     currentState = "ADC_current_state.json", \
#     previousState = "ADC_previous_state.json",
# )
SCLK = 0x01
MOSI = 0x02
MISO = 0x04
CS = 0x08
spiAdc = GpioSyncController()
spiAdc.configure('ftdi:///1', direction=(SCLK|MOSI|CS), frequency=1e3)
adc = FTDISPI.Interface( \
    FTDISPI.GPIO(
        spiAdc, \
        SCLK = SCLK, \
        MOSI = MOSI, \
        MISO = MISO, \
        CS = CS, \
    ), \
    defaultMap  = "ADC12J2700.json", \
    currentState = "ADC_current_state.json", \
    previousState = "ADC_previous_state.json",
)


SCLK = 0x01
MOSI = 0x02
MISO = 0x80 # jumper soldered from Status_LD1 pin to FT4232HL (pin 46)
CS = 0x04

lmkAdc = GpioSyncController()
# lmkAdc = SpiController()
lmkAdc.configure('ftdi:///3', direction=(SCLK|MOSI|CS), frequency=1e4)
# lmkAdc.configure('ftdi:///2')

lmk = FTDISPI.Interface( \
    FTDISPI.GPIO(
        lmkAdc, \
        SCLK = SCLK, \
        MOSI = MOSI, \
        MISO = MISO, \
        CS = CS, \
    ), \
# slaveLmk= lmkAdc.get_port( \
#     cs=0, \
#     freq=1e6, \
#     mode=0 \
# )
# lmk = FTDISPI.Interface( \
#     FTDISPI.MPSSE(slaveLmk), \
    defaultMap  = "LMK_ADC_config_using_LMK_DAC.json", \
    currentState = "LMK_current_state.json", \
    previousState = "LMK_previous_state.json",
)

# FTDISPI.uiLoop( lmk )


print("\n**** ADC12J2700EVM SPI Register Config ****")
ui = [""]
help = True
while (ui[0] != "exit"):
    print("\nEnter device [ adc | lmk ] or exit:\n\n> ", end='')
    ui = sys.stdin.readline().rstrip().split(' ')
    if ui[0] == "adc":
        print( "\n*** ADC ***")
        FTDISPI.uiLoop( adc, printHelp=help )
        help=False
    if ui[0] == "lmk":
        print( "\n*** LMK ***")
        FTDISPI.uiLoop( lmk, printHelp=help )
        help=False
