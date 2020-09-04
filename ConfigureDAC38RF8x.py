import time
import sys
import FTDISPI
import JSONFile
from pyftdi.spi import SpiController


spi = SpiController()
spi.configure('ftdi:///2')

dac = FTDISPI.Device( \
    slave       = spi.get_port(cs=0, freq=1E6, mode=0), \
    defaultMap  = "DAC38RF8x.json", \
    currentState = "DAC_current_state.json", \
    previousState = "DAC_previous_state.json",
)



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


def dispChanges():
    dac.compare(pre_display="\n*** All changes ***", post_display="---------------")


def startupSequence():
    dac.readState(display=False)
    ###############################
    print ( \
        "SPI_TXENABLE set to 0 (OR'd with TXENABLE pin)" \
    )
    dac.writeBits( \
        'JESD_FIFO',        ['XXXXXXXX', 'XXXXXXX0'] \
    )
    dispChanges()
    ###############################
    while(1):
        input( "Depress RESETB push-button (press <ENTER>)" )
        struct = dac.readStruct({'VENDOR_VER':{}}, display=True)
        if (struct['VENDOR_VER']['data'][0] & 0xFC == 0x80): # 100000XX XXXXXXXX
            break
    pllMode = input( "Use PLL? [y/N]\n> " )
    dac.writeBits( \
        'CLK_PLL_CFG',      ['XXXXX1XX', 'XXXXXXXX'] \
    )
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
    dispChanges()
    ###############################
    print( \
        "JESD core in reset..." \
    )
    dac.writeBits( \
        'RESET_CONFIG',     ['XXXXXXXX', 'XXXXX111'] \
    )
    dispChanges()
    ###############################
    print( \
        "Synchronizing CDRV and JESD204B blocks..." \
    )
    dac.writeBits( \
        'SYSREF_CLKDIV',    ['XXXXXXXX', 'X010XXXX'] \
    )
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    dac.writeBits( \
        'SYSREF_CLKDIV',    ['XXXXXXXX', 'XXXXX011'] \
    )
    dispChanges()
    input( \
        "Ensure 2 SYSREF edges... (press <ENTER>)" \
    )
    ###############################
    print( \
        "Taking JESD204B core out of reset..." \
    )
    dac.writeBits( \
        'RESET_CONFIG',     ['1XXXXXXX', 'XXXXXX11'] \
    )
    dispChanges()
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
    dispChanges()
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
print("write <REG_NAME> XXXX1010 1XXXXXX0       | Write bits (any char not 0 or 1 is a don't-care)")
print("read <REG_NAME>                          | Read register")
print("all                                      | Read all registers")
print("save <fileName>                          | Save registers to JSON file")
print("load <fileName>                          | Load and write registers from JSON file")
print("loadDefault                              | Load datasheet default JSON configuration")
print("startup                                  | Step through DAC startup sequence")
print("exit                                     | Exit the program")
print()
print()

ui = [""]
while (ui[0] != "exit"):
    print("\n> ", end='')
    ui = sys.stdin.readline().rstrip().split(' ')

    if (ui[0] == "read"):
        dac.readStruct({ ui[1] : {} }, display=True)
    if (ui[0] == "write"):
        dac.writeBits( ui[1], [ ui[2], ui[3] ] )
    if (ui[0] == "all"):
        dac.readState()
    if (ui[0] == "compare"):
        dac.compare()
    if (ui[0] == "trigger"):
        while(1):
            dac.trigger(pre_display=chr(27)+"[2J")
            time.sleep(.5)
            if not sys.stdin.isatty():
                break
    if (ui[0] == "save"):
        if dacJSON is None:
            if len(ui) > 1:
                dacJSON = JSONFile.new(ui[1])
            else:
                dacJSON = JSONFile.new(input("\nSave as: "))
        dacJSON.write( dac.readState() )
    if (ui[0] == "load"):
        if dacJSON is None:
            dacJSON = JSONFile.load(ui[1])
        dac.writeStruct(dacJSON.read())
        dac.readState()
    if (ui[0] == "loadDefault"):
        dac.writeDefault()
    if (ui[0] == "startup"):
        startupSequence()
