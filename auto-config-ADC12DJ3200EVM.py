from gpiozero import LED
from signal import pause
from datetime import datetime

from time import sleep
import os

# Active-low reset
comeOutOfReset = DigitalOutputDevice(18, active_high=True)

red = LED(2, active_high=False)
green = LED(4, active_high=False)
blue = LED(3, active_high=False)

red.blink()
#sleep(10)


os.system('printf "all\nloadCSV lmk_config.csv\nexit\n" | python3 ConfigureLMK_ADC12DJ3200EVM.py > lmk.log')
sleep(5)
os.system('printf "loadCSV lmx_config.csv\nexit\n" | python3 ConfigureLMX_ADC12DJ3200EVM.py > lmx.log')
sleep(5)
os.system('printf "all\nloadCSV adc_config_SFORMAT.csv\nexit\n" | python3 ConfigureADC_ADC12DJ3200EVM.py > adc.log')

red.off()
green.on()

sleep(5)
comeOutOfReset.on()

pause()
