import pymongo, json
import os,re
# print(os.getcwd())
import sys
sys.path.append('../utils/')
from fileWritingUtil import removeAndWriteFile

if __name__ == "__main__":
    with open('../config/database.json') as json_data_file:
        dbConfig = json.load(json_data_file)
    dsdb = dbConfig["mikelab"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]
    colList = db.list_collection_names()
    print(colList)
    path = './initialize/'
    avoidnames = [ re.sub(r'import_|.js',"",fname) for fname in os.listdir(path)]
    avoidnames.extend([
        'classified_thread_160420',
        'classified_thread_20200518',
        'classified_thread_180420',
        'selected_threads_20200307',
        'classified_thread_090120',
        'classified_thread_251119'

    ])
    print(avoidnames)
    targetCols = [ col for col in colList if col not in avoidnames] # not in folder
    print(targetCols)
    for colName in targetCols:
        if colName in colList:
            currentCol = db[colName]
            print(colName, ":retrieve labeled threads ...")
            currentDocs = currentCol.find({}, no_cursor_timeout=True)
            print(colName, ": finish retrieving")
            lines = ""
            # datetimeRex = r'datetime.datetime\((\d+),\s+(\d+),\s+(\d+),\s+(\d+),\s+(\d+)[,\s\d]*\)'
            for doc in currentDocs:
                lines += "db."+colName+".insert("+str(doc)+");\n".replace(" ","").replace(r'datetime\.datetime','new Date').replace('None','null')

        removeAndWriteFile(path+"import_"+colName+".js", lines, "js")