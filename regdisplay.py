
##########################################
# Format and print the contents of
# a register (units of bytes).
##########################################

def printByte(aByte):
    for aBit in range(8):
        if ((aByte >> (7-aBit)) & 0x01):
            print("1 ", end='')
        else:
            print("_ ", end='')

# def printHex(aByteArray):
#     for aByte in aByteArray:
#         print(hex(aByte))
#
def printReg(addrName, addr=[], data=[], note="", nameColWidth=18):
    print( addrName+(" "*(nameColWidth-len(addrName))), end=' ')
    for a in addr:
        print("0x{:02x}".format(a), end=' ')
    print('  |  ', end='')
    for d in data:
        print("0x{:02x}".format(d), end=' ')
        printByte(d)
    print('  |  '+note)



##########################################
# Wrapper functions to print the result of
# functions that return a list of register
# bytes.
##########################################

# def printRead(func, reg):
#     readData = func(reg)
#     printReg( reg, data=readData )
#     return readData

def printAction(func, reg, upper=0x00, lower=0x00):
    readData = func(reg, upper, lower)
    printReg( reg, data=readData )
    return readData


##########################################
# Print data structured as:
#  {
#     # read only operation
#     'REG0' : {},
#     # write-read operation
#     'REG1' : {
#         'data' : [ 0x08, 0x22 ]
#     },
#     # write-read operation with mask
#     'REG2' : {
#         'mask' : [ 0x0F, 0xFF ],
#         'data' : [ 0x08, 0x22 ]
#     }
#  }
##########################################

def printData(regData):
    for name in regData:
        if 'new_data' in regData[name]:
            printReg(name, addr=regData[name]['addr'], data=regData[name]['data'], note=regData[name]['info'])
            printReg("--> "+name, addr=regData[name]['addr'], data=regData[name]['new_data'], note=regData[name]['info'])
        else:
            printReg(name, addr=regData[name]['addr'], data=regData[name]['data'], note=regData[name]['info'])
