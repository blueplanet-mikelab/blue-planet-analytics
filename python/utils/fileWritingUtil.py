import os
import json

def writeTXTFile(fname, content):
    f = open(fname, "w",encoding='utf-8')
    f.write(content)
    print("create",fname,"success")
    f.close()

def writeJSONFile(fname, content):
    with open('./'+fname, 'w', encoding="utf8") as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4)
        print("create",fname,"success")

def writeJSFile(fname, content):
    with open('./'+fname, 'w', encoding="utf8") as outfile:
            outfile.write(content)
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
    else:
        print("invalid file type")