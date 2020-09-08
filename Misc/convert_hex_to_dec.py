import JSONFile


lmkFile = JSONFile.load("LMK_default.json")


def convert_list_to_int(strList):
    for i in range(len(strList)):
        strList[i] = int(strList[i], 16)

lmk = lmkFile.read()
for reg in lmk.keys():
    convert_list_to_int(lmk[reg]['addr_w'])
    convert_list_to_int(lmk[reg]['addr_r'])
    convert_list_to_int(lmk[reg]['pre_r'][0]['0x0000'])
    convert_list_to_int(lmk[reg]['pre_r'][1]['0x0104'])

lmkFile.write()
