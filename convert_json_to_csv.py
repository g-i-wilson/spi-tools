import JSONFile
import sys


inputFile = JSONFile.load(sys.argv[1])
writeFile = open(sys.argv[2]+"_write.csv", "w")
readFile = open(sys.argv[2]+"_read.csv", "w")



def intList(theList):
    print(theList)
    str = ""
    for theInt in theList:
        str += "0x{:02x}".format(theInt)+","
    return str

struct = inputFile.read()
for reg in struct.keys():
    writeFile.write( intList(struct[reg]['addr_w']) + intList(struct[reg]['data'])[0:-1] + "\n" )
    readFile.write( intList(struct[reg]['addr_r']) + ("0x00,"*len(struct[reg]['data']))[0:-1] + "\n" )
    # print( intList(struct[reg]['addr_w']) + "," + intList(struct[reg]['data']) )
    # print( intList(struct[reg]['addr_r']) + ",0x00"*len(struct[reg]['data']) )

writeFile.close()
readFile.close()
