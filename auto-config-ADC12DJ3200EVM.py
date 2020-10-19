from gpiozero import RGBLED
from time import sleep
import os


led = RGBLED(red=3, blue=5, green=7, active_high=False)

led.color = (1, 1, 0)
led.blink()

os.system('printf "all\nloadCSV lmk_config.csv\nexit\n" | python3 ConfigureLMK_ADC12DJ3200EVM.py')
sleep(5)
os.system('printf "loadCSV lmx_config.csv\nexit\n" | python3 ConfigureLMX_ADC12DJ3200EVM.py')
sleep(5)
os.system('printf "all\nloadCSV adc_config_SFORMAT.csv\nexit\n" | python3 ConfigureADC_ADC12DJ3200EVM.py')

led.color = (0, 1, 0)

pause()
