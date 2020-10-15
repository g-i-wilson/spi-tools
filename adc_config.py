import time
import sys
from pyftdi.spi import SpiController
from pyftdi.gpio import GpioSyncController
import FTDISPI


spiAdc = SpiController()
spiAdc.configure('ftdi:///1')
slaveAdc = spiAdc.get_port( \
    cs=0, \
    freq=1e6, \
    mode=0 \
)
adc = FTDISPI.Interface( \
    FTDISPI.MPSSE(slaveAdc), \
    defaultMap  = "ADC12DJ3200.json", \
    currentState = "ADC12DJ3200_current_state.json", \
    previousState = "ADC12DJ3200_previous_state.json",
)


adc.writeCSV(sys.argv[1])
print("*** ADC ***")
adc.readState()
