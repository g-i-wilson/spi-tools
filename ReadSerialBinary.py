import sys
import serial
import time

io = serial.Serial(port=sys.argv[1], baudrate=sys.argv[2])

while (1):
    sys.stdout.buffer.write(io.read(io.inWaiting()))
    sys.stdout.buffer.flush()
    time.sleep(0.1)
