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


# lmk.readState()








def ui_hex(str):
    return int(str,16)

lmkJSON = None



print("**** LMK0428 SPI Register Config ****")
print()
print("Command set:")
print("write <REG_NAME> XXXX1010 1XXXXXX0       | Write bits (any char not 0 or 1 is a don't-care)")
print("read <REG_NAME>                          | Read register")
print("all                                      | Read all registers")
print("save <fileName>                          | Save registers to JSON file")
print("load <fileName>                          | Load and write registers from JSON file")
print("loadDefault                              | Load datasheet default JSON configuration")
print("exit                                     | Exit the program")
print()
print()

ui = [""]
while (ui[0] != "exit"):
    print("\n> ", end='')
    ui = sys.stdin.readline().rstrip().split(' ')

    if (ui[0] == "read"):
        lmk.readStruct({ ui[1] : {} }, display=True)
    if (ui[0] == "write"):
        lmk.writeBits( ui[1], [ ui[2], ui[3] ] )
    if (ui[0] == "all"):
        lmk.readState()
    if (ui[0] == "compare"):
        lmk.compare()
    if (ui[0] == "trigger"):
        while(1):
            lmk.trigger(pre_display=chr(27)+"[2J")
            time.sleep(1)
    if (ui[0] == "save"):
        if lmkJSON is None:
            if len(ui) > 1:
                lmkJSON = JSONFile.new(ui[1])
            else:
                lmkJSON = JSONFile.new(input("\nSave as: "))
        lmkJSON.write( lmk.readState() )
    if (ui[0] == "load"):
        if lmkJSON is None:
            lmkJSON = JSONFile.load(ui[1])
        lmk.writeStruct(lmkJSON.read())
        lmk.readState()
    if (ui[0] == "loadDefault"):
        lmk.writeDefault()
