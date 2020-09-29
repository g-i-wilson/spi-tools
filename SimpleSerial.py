import sys
import serial

port = "/dev/ttyUSB0"
io = serial.Serial(port=port, baudrate="9600")

ui = [""]
while (1):
    try:
        ui = sys.stdin.readline().rstrip().split(' ')
        if ui[0].lower() == "exit":
            exit()
        for hexWord in ui:
            io.write(int(hexWord,16).to_bytes(1,'big'))
    except:
        pass
    print(io.read(1))
