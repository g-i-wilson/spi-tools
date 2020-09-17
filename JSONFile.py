import sys
import json

debug = False

def new(filePath):
    obj = JSONFile(filePath)
    obj.write()
    return obj

def load(filePath):
    obj = JSONFile(filePath)
    obj.load()
    return obj


def mergeOldIntoNew(new={}, old={}):
    if debug:
        print(new)
        print(old)
    for key in old.keys():
        if not key in new.keys():
            try:
                test = old[key].keys()
                new[key] = {}
                mergeOldIntoNew(new[key], old[key])
            except:
                new[key] = old[key]


class JSONFile:
    def __init__(self, filePath, data={}):
        self.filePath = filePath
        self.data = data
        self.exists = False
        if debug:
            print("Initialized JSONFile object with filepath string '"+filePath+"'")
    def load(self):
        ret = None
        file = None
        try:
            file = open(self.filePath, "r")
            self.data = json.load(file)
            ret = self.data
            self.exists = True
        except:
            if debug:
                print("Failed to read from: "+self.filePath)
        finally:
            if file:
                file.close()
        return ret
    def read(self):
        return self.data
    def write(self, data=None):
        ret = None
        if data:
            self.data = data
        try:
            file = open(self.filePath, "w")
            json.dump(self.data, file)
            ret = self.data
            self.exists = True
        except:
            if debug:
                print("Failed to write to: "+filePath)
        finally:
            file.close()
        return ret
    def writeStr(self, str):
        try:
            jsonData = json.loads(str)
            return self.write(jsonData)
        except:
            if debug:
                print("Failed to parse JSON string: "+str)
            return None
    def merge(self, data):
        if debug:
            print(data)
        mergeOldIntoNew(new=data, old=self.data)
        return self.write(data)
    def mergeStr(self, jsonStr):
        try:
            data = json.loads(jsonStr)
            return self.merge(data)
        except:
            if debug:
                print("Failed to parse JSON string: "+str)
            return None
    def fileExists(self):
        return self.exists


if __name__== "__main__":
    if debug:
        test0 = {"key0":10}
        test1 = {"key1":{"key2":{"key3a":11,"key3b":{"key4":12}}}}
        mergeOldIntoNew(test0,test1)
        print(test0)
    if len(sys.argv) == 1:
        filePath = sys.stdin.readline().rstrip()
        jsonFile = new(filePath)
        while(1):
            input = sys.stdin.readline().rstrip()
            print(jsonFile.mergeStr(input))
    if len(sys.argv) == 2:
        print(load(sys.argv[1]).read())
    if len(sys.argv) == 3:
        obj = new(sys.argv[1])
        print(obj.writeStr(sys.argv[2]))
