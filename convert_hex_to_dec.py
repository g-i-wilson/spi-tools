import JSONFile
import sys

convertFile = JSONFile.load(sys.argv[1])
# print(convertFile.read())

def convert_list_to_int(strList):
    for i in range(len(strList)):
        print(strList[i])
        strList[i] = int(strList[i], 16)

struct = convertFile.read()
for reg in struct.keys():
    convert_list_to_int(struct[reg]['addr_w'])
    convert_list_to_int(struct[reg]['addr_r'])
    convert_list_to_int(struct[reg]['data'])
    # convert_list_to_int(struct[reg]['pre_r'][0]['0x0000'])
    # convert_list_to_int(struct[reg]['pre_r'][1]['0x0104'])

print(struct)
convertFile.write()
