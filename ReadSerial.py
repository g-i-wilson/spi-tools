import sys
import serial

io = serial.Serial(port=sys.argv[1], baudrate=sys.argv[2])

groupSize = 3

if len(sys.argv) > 3:
    groupSize = int(sys.argv[3])

file = None
if len(sys.argv) > 4:
    file = open(sys.argv[4], "wb")



byteNumber = 0
while (1):
    # waiting = io.inWaiting()
    # print(io.inWaiting())
    if (io.inWaiting()>0):
        # print("data!")
        byteNumber += 1
        if file:
            file.write( io.read() )
        else:
            # sys.stdout.buffer.write( io.read(1) )
            # sys.stdout.flush()
            theByte = io.read()
            if byteNumber < groupSize:
                print( "0x{:02x}".format(int.from_bytes(theByte,'big')), end=',' )
            elif byteNumber == groupSize:
                print( "0x{:02x}".format(int.from_bytes(theByte,'big')), end='' )
                byteNumber = 0
                print()
