import time
import sys
from pyftdi.spi import SpiController
import FTDISPI


spiAdc = SpiController()
spiLmk = SpiController()

spiAdc.configure('ftdi:///1')
slaveAdc = spiAdc.get_port( \
    cs=0, \
    freq=1e6, \
    mode=0 \
)
spiLmk.configure('ftdi:///2')
slaveLmk = spiLmk.get_port( \
    cs=0, \
    freq=1e6, \
    mode=0 \
)

adc = FTDISPI.Interface( \
    FTDISPI.MPSSE(slaveAdc), \
    defaultMap  = "ADC12J2700.json", \
    currentState = "ADC_current_state.json", \
    previousState = "ADC_previous_state.json",
)
lmk = FTDISPI.Interface( \
    FTDISPI.MPSSE(slaveLmk), \
    defaultMap  = "LMK04828.json", \
    currentState = "LMK_current_state.json", \
    previousState = "LMK_previous_state.json",
)




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
