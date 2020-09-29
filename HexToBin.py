import sys


ui = [""]
while (1):
    ui = sys.stdin.readline().rstrip().split(' ')
    for hexWord in ui:
        sys.stdout.buffer.write(int(hexWord,16).to_bytes(1,'big'))
        sys.stdout.buffer.flush()
