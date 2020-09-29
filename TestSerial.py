import serial

port = "/dev/ttyUSB0"
io = serial.Serial(port=port, baudrate="9600")

if io.is_open:
    io.close()

io.open()

io.write([0x02, 0x01, 0xF1, 0x0A])
io.flush()
io.write([0x18, 0x0A])
io.flush()

while(1):
    if io.inWaiting():
        print(io.read(1))