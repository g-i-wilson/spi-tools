import sys
import serial

io = serial.Serial(port=sys.argv[1], baudrate=sys.argv[2])

file = None
if len(sys.argv) > 3:
    file = open(sys.argv[3], "wb")

while (1):
    if file:
        file.write( io.read(1) )
    else:
        # sys.stdout.buffer.write( io.read(1) )
        # sys.stdout.flush()
        theByte = io.read(1)
        if theByte != b'\n':
            print( "0x{:02x}".format(int.from_bytes(theByte,'big')), end=',' )
        else:
            print()
