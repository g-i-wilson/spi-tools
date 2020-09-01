import time
import sys
import DAC38RF8x
from regdisplay import *

##########################################
# SPI configuration class
##########################################

dacSpi = DAC38RF8x.SpiConfig()


##########################################
# Class to tune VCO
##########################################

def VCO_OK(Tj, LFVOLT):
    if (Tj >= 108 and (LFVOLT == 5 or LFVOLT == 6)):
        return True
    elif (Tj >= 92 and (LFVOLT == 4 or LFVOLT == 5)):
        return True
    elif (Tj >= 26 and (LFVOLT == 3 or LFVOLT == 4)):
        return True
    elif (LFVOLT == 2 or LFVOLT == 3):
        return True
    else:
        return False

class VCOTuner:
    def __init__(self,VCOLow, VCOHigh, VCOInc):
        self.VCOLow = VCOLow
        self.VCOHigh = VCOHigh
        self.VCOInc = VCOInc
        self.VCOFreq = VCOLow
    def value(self):
        return self.VCOFreq
    def tune(self):
        while(1):
            PLL_CONFIG = printRead(0x06)
            writeReg(0x33, self.VCOFreq, PLL_CONFIG[1])
            TEMP_PLLVOLT = readReg(0x06)
            TEMPDATA = TEMP_PLLVOLT[0]
            PLL_LFVOLT = (TEMP_PLLVOLT[1] >> 5)
            # print( ("\b"*100)+"Freq: "+str(self.VCOFreq)+", TEMPTDATA: "+str(TEMPDATA)+", PLL_LFVOLT: "+str(PLL_LFVOLT), end='' )
            print( "Freq: "+str(self.VCOFreq)+", TEMPTDATA: "+str(TEMPDATA)+", PLL_LFVOLT: "+str(PLL_LFVOLT) )
            self.VCOFreq += self.VCOInc
            if (VCO_OK(TEMPDATA, PLL_LFVOLT) or self.VCOFreq >= self.VCOHigh):
                break
        print()





# def startupSequence():
    # print ("SPI_TXENABLE set to 0 (OR'd with TXENABLE pin)")
    # # printAction( bitOn, 0x0D, 0x00, 0x01)
    # printAction(dacSpi.action({'JESD_FIFO' : {'mask':0x01, 'data':0x01}})
    # while(1):
    #     if input("Depress RESETB push-button (press <ENTER>)\n> ") == "cancel":
    #         return
    #     VENDOR_VER = printRead(dacSpi.readPageReg, 'VENDOR_VER')
    #     if (VENDOR_VER[0] & 0xFC == 0x80): # 0b100000XX
    #         break
    # pllMode = input("Tune PLL? [y/N]\n> ")
    # if (pllMode.lower() == "y"):
    #     t = VCOTuner(0x10, 0x40, 0x01)
    #     t.tune()
    # if input("Start SYSREF generation... (press <ENTER>)\n> ") == "cancel":
    #     return
    # print( "Encoder block in reset...")
    # printAction( bitOff, 0x24, 0x00, 0x70)
    # printAction( bitOff, 0x5C, 0x00, 0x07)
    # printAction( bitOn, 0x0A, 0x80, 0x00)
    # if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
    #     return
    # printAction( bitOff, 0x0A, 0x80, 0x00)
    # print( "JESD core in reset...")
    # printAction( bitOn, 0x00, 0x00, 0x03)
    # print( "Synchronizing CDRV and JESD204B blocks...")
    # SYSREF_CLKDIV = readReg(0x24)
    # printAction( writeReadReg, 0x24, SYSREF_CLKDIV[0], (SYSREF_CLKDIV[1] & ~0x70) | 0x20 ) # X010XXXX
    # if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
    #     return
    # printAction( writeReadReg, 0x5C, SYSREF_CLKDIV[0], (SYSREF_CLKDIV[1] & ~0x07) | 0x03 ) # XXXXX011
    # if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
    #     return
    # print( "Taking JESD204B core out of reset...")
    # printAction( bitOff, 0x00, 0x00, 0x03 )
    # if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
    #     return
    # print( "Clearing all DAC alarms...")
    # rangeAction( writeReadReg, 0x04, 0x05, 0x00, 0x00)
    # rangeAction( writeReadReg, 0x64, 0x6D, 0x00, 0x00)
    # if input("Stop SYSREF generation (optional)... (press <ENTER>)\n> ") == "cancel":
    #     return
    # print( "SPI_TXENABLE set to 1 (OR'd with TXENABLE pin)...")
    # printAction( bitOn, 0x0D, 0x00, 0x01)
    # print( "Done." )




print("**** DAC38RF8x SPI Register Config ****")
print()
print("Command set:")
print("write <ADDR> <upperByte> <lowerByte>     | Write register")
print("enable4Wire                              | Enables 4-wire mode (called when program starts)")
print("read <ADDR>                              | Read register (4-wire mode only)")
print("on <ADDR> <upperMask> <lowerMask>        | Set bit to 1 (4-wire mode only)")
print("off <ADDR> <upperMask> <lowerMask>       | Set bit to 0 (4-wire mode only)")
print("readAll                                  | Read all registers")
print("enableAll                                | Enable all register pages")
print("save <fileName>                          | Save registers to a file (4-wire mode only)")
print("load <fileName>                          | Load and write registers from a file")
print("loadDefault                              | Load datasheet default configuration")
print("spiReset                                 | Write 0x80 0x00 to address 0x00")
print("exit                                     | Exit the program")
print()
print()

ui = [""]
while (ui[0] != "exit"):
    print("\n> ", end='')
    ui = sys.stdin.readline().rstrip().split(' ')
    command = ui[0]
    register = ""
    uiVal = [0,0,0]
    if len(ui)>1:
        register = ui[1]
    for i in range(1, len(ui)):
        uiVal[i-1] = int(ui[i],16)

    if (command == "duc"):
        dacSpi.setDUC(uiVal[0])
    if (command == "read"):
        printRead( dacSpi.readPageReg, register )
    if (command == "write"):
        printAction( dacSpi.writeReadPageReg, register, uiVal[1], uiVal[2] )
    if (command == "on"):
        printAction( dacSpi.bitsOn, register, uiVal[1], uiVal[2] )
    if (command == "off"):
        printAction( dacSpi.bitsOff, register, uiVal[1], uiVal[2] )
    if (command == "readAll"):
        printData(dacSpi.readDataAll())
    if (command == "save"):
        outputFile = open(ui[1], "w")
        allData = dacSpi.readDataAll()
        for reg in allData:
            outputFile.write(reg+","+hex(allData[reg]['data'][0])+","+hex(allData[reg]['data'][1])+"\n")
        outputFile.close()
    if (command == "load"):
        inputFile = open(ui[1], "r")
        inputRegMap = inputFile.readlines()
        for regData in inputRegMap:
            reg = regData.rstrip().split(',')
            dacSpi.writePageReg(reg[0], int(reg[1],16), int(reg[2],16))
        inputFile.close()
        printData(dacSpi.readDataAll())
    # if (command == "loadDefault"):
    #     # for aReg in defaultMap:
    #     #     writeReg(aReg[0], aReg[1], aReg[2])
    #     # enableAll()
    #     # readAll()
    # if (command == "enableAll"):
    #     # enableAll()
    #     # readAll()
    # if (command == "spiReset"):
    #     # spiReset()
    # if (command == "enable4Wire"):
    #     # enable4Wire()
    # if (command == "zeroRange"):
    #     # rangeWrite(writeReadReg, uiVal[0], uiVal[1], 0x00, 0x00)
    if (command == "startup"):
        startupSequence()
