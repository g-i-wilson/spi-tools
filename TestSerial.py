import serial
import sys

io = serial.Serial(port=sys.argv[1], baudrate="9600")

if io.is_open:
    io.close()

io.open()

#io.write([0x02, 0x01, 0xF1, 0x0A])
io.write([0x02])
io.write([0x0])
io.write([0x55])
#io.write([0x0A])
io.flush()

while(not io.inWaiting()):
    pass
print(io.read(1))

while(not io.inWaiting()):
    pass
print(io.read(1))

while(not io.inWaiting()):
    pass
print(io.read(1))

#io.write([0x18, 0x0A])
io.write([0x18])
io.flush()

while(not io.inWaiting()):
    pass
print(io.read(1))
