#!/usr/bin/env bash

cd ~/spi-tools/
printf "loadDefault\nloadCSV lmk_config.csv\nexit\n" | python3 ConfigureLMK_ADC12DJ3200EVM.py
printf "loadDefault\nloadCSV adc_config.csv\nexit\n" | python3 ConfigureADC_ADC12DJ3200EVM.py
