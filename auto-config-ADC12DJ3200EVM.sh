#!/usr/bin/env bash

printf "all\nloadCSV lmk_config.csv\nexit\n" | python3 ConfigureLMK_ADC12DJ3200EVM.py
sleep 5
printf "loadCSV lmx_config.csv\nexit\n" | python3 ConfigureLMX_ADC12DJ3200EVM.py
sleep 5
printf "all\nloadCSV adc_config_SFORMAT.csv\nexit\n" | python3 ConfigureADC_ADC12DJ3200EVM.py
