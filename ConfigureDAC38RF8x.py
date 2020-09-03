import time
import sys
import FTDISPI
import JSONFile

##########################################
# SPI configuration class
##########################################

dac = FTDISPI.Device(defaultMap="DAC38RF8x.json")



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



def startupSequence():
    ###############################
    print ( \
        "SPI_TXENABLE set to 0 (OR'd with TXENABLE pin)" \
    )
    dac.writeBits( \
        'JESD_FIFO',        ['XXXXXXXX', 'XXXXXXX0'] \
    )
    ###############################
    while(1):
        input( "Depress RESETB push-button (press <ENTER>)" )
        struct = dac.readStruct({'VENDOR_VER':{}})
        if (struct['VENDOR_VER']['data'][0] & 0xFC == 0x80): # 100000XX XXXXXXXX
            break
    pllMode = input( "Tune PLL? [y/N]\n> " )
    if (pllMode.lower() == "y"):
        vcoLow = 0x10
        vcoHigh = 0x40
        vcoIncrement = 0x01
        vcoFreq = 0x00
        while(1):
            dac.writeStruct({'PLL_CONFIG2':{'data':[vcoFreq,0x00], 'mask':[0x7F,0x00]}}) # X_______ XXXXXXXX
            tempVoltage     = dac.readStruct({'TEMP_PLLVOLT':{}})
            TEMPDATA        = tempVoltage['TEMP_PLLVOLT']['data'][0]
            PLL_LFVOLT      = tempVoltage['TEMP_PLLVOLT']['data'][1] >> 5
            print( "Freq: "+str(vcoFreq)+", TEMPTDATA: "+str(TEMPDATA)+", PLL_LFVOLT: "+str(PLL_LFVOLT) )
            vcoFreq += vcoIncrement
            if VCO_OK(TEMPDATA, PLL_LFVOLT):
                break
            elif vcoFreq >= vcoHigh:
                print( "Max VCO freq reached" )
                break
    ###############################
    input( \
        "Start SYSREF generation... (press <ENTER>)" \
    )
    ###############################
    print( \
        "Encoder block in reset..." \
    )
    dac.writeBitsList([ \
        ['SYSREF_CLKDIV',   ['XXXXXXXX', 'X000XXXX']], \
        ['JESD_SYSR_MODE',  ['XXXXXXXX', 'XXXXX000']], \
        ['MULTIDUC_CFG1',   ['1XXXXXXX', 'XXXXXXXX']], \
    ])
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    dac.writeBits( \
        'CLK_CONFIG',       ['1XXXXXXX', 'XXXXXXXX'] \
    )
    ###############################
    print( \
        "JESD core in reset..." \
    )
    dac.writeBits( \
        'RESET_CONFIG',     ['XXXXXXXX', 'XXXXX111'] \
    )
    ###############################
    print( \
        "Synchronizing CDRV and JESD204B blocks..." \
    )
    dac.writeBits( \
        'SYSREF_CLKDIV'     ['XXXXXXXX', 'X010XXXX'] \
    )
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    dac.writeBits( \
        'SYSREF_CLKDIV'     ['XXXXXXXX', 'XXXXX011'] \
    )
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    ###############################
    print( \
        "Taking JESD204B core out of reset..." \
    )
    dac.writeBits( \
        'RESET_CONFIG',     ['1XXXXXXX', 'XXXXXX11'] )
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    ###############################
    print( \
        "Clearing all alarms..." \
    )
    dac.writeBitsList([ \
        ['ALM_SD_DET',      ['00000000', '00000000']], \
        ['ALM_SYSREF_DET',  ['00000000', '00000000']], \
        ['JESD_ALM_L0',     ['00000000', '00000000']], \
        ['JESD_ALM_L1',     ['00000000', '00000000']], \
        ['JESD_ALM_L2',     ['00000000', '00000000']], \
        ['JESD_ALM_L3',     ['00000000', '00000000']], \
        ['JESD_ALM_L4',     ['00000000', '00000000']], \
        ['JESD_ALM_L5',     ['00000000', '00000000']], \
        ['JESD_ALM_L6',     ['00000000', '00000000']], \
        ['ALM_SYSREF_PAP',  ['00000000', '00000000']], \
        ['ALM_CLKDIV1',     ['00000000', '00000000']], \
    ])
    input( \
        "Stop SYSREF generation (optional)... (press <ENTER>)" \
    )
    print( \
        "SPI_TXENABLE set to 1 (OR'd with TXENABLE pin)..." \
    )
    dac.writeBits( \
        'JESD_FIFO', ['XXXXXXXX', 'XXXXXXX1'] \
    )
    ###############################
    print( \
        "Done." \
    )





def ui_hex(str):
    return int(str,16)

dacJSON = None

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

    if (ui[0] == "duc"):
        dacSpi.setDUC(int(ui[1],16))
    if (ui[0] == "read"):
        printRead( dacSpi.readPageReg, ui[1] )
    if (ui[0] == "write"):
        writeData = { ui[1] : { 'data':[ int(ui[2],16), int(ui[3],16) ] } }
        FTDISPI.printStruct( dac.writeStruct(writeData) )
    if (ui[0] == "writeBits"):
        writeData = { ui[1] : { 'data':[ int(ui[2],16), int(ui[3],16) ], 'mask':[ int(ui[4],16), int(ui[5],16) ] } }
        FTDISPI.printStruct( dac.writeStruct(writeData) )
    if (ui[0] == "on"):
        printAction( dacSpi.bitsOn, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "off"):
        printAction( dacSpi.bitsOff, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "readAll"):
        printData( dacSpi.outRegData() )
    if (ui[0] == "save"):
        if dacJSON is None:
            if len(ui) > 1:
                dacJSON = JSONFile.new(ui[1])
            else:
                dacJSON = JSONFile.new(input("\nSave as: "))
        dacJSON.write( dac.currentState() )
    if (ui[0] == "load"):
        if dacJSON is None:
            dacJSON = JSONFile.load(ui[1])
        dac.writeStruct(dacJSON.read())
        dac.currentState()
    if (ui[0] == "loadDefault"):
        dac.writeDefault()
    if (ui[0] == "startup"):
        startupSequence()
