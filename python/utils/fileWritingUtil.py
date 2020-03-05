import os
import json, csv
from bson import json_util

def writeTXTFile(fname, content):
    f = open(fname, "w",encoding='utf-8')
    f.write(content)
    print("create",fname,"success")
    f.close()

def writeJSONFile(fname, content):
    with open('./'+fname, 'w', encoding="utf8") as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4, default=json_util.default)
        print("create",fname,"success")

def writeJSFile(fname, content):
    with open('./'+fname, 'w', encoding="utf8") as outfile:
        outfile.write(content)
        print("create",fname,"success")

def writeCSVFile(fname, content):
    with open('./'+fname, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(content)
        print("create",fname,"success")


def removeFile(fname):
    if os.path.isfile(fname):
        os.remove(fname)
        print("remove",fname,"success")

def removeAndWriteFile(fname, content, ftype='json'):
    removeFile(fname)

    if ftype == 'txt':
        writeTXTFile(fname, content)
    elif ftype == 'json':
        writeJSONFile(fname, content)
    elif ftype == 'js':
        writeJSFile(fname, content)
    elif ftype == 'csv':
        writeCSVFile(fname, content)
    else:
        print("invalid file type")


def readTXTFile(fname):
    f = open(fname, "r",encoding='utf-8')
    content = f.read()
    print("read",fname,"success")
    f.close()
    return content

def readJSONFile(fname):
    with open(fname,'r', encoding="utf8") as json_file:
        return json.load(json_file) 