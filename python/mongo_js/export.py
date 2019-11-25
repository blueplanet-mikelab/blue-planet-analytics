import pymongo, json
import os,re
print(os.getcwd())
import sys
sys.path.append('../utils/')
from fileWritingUtil import removeAndWriteFile

if __name__ == "__main__":
    with open('../config/database.json') as json_data_file:
        dbConfig = json.load(json_data_file)
    dsdb = dbConfig["pantip-ds"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]
    colList = db.list_collection_names()

    targetCols = ["classified_thread_251119", "travel_guide_average_071119"]
    for colName in targetCols:
        if colName in colList:
            currentCol = db[colName]
            print("retrieve labeled threads ...")
            currentDocs = currentCol.find({})
            lines = ""
            # datetimeRex = r'datetime.datetime\((\d+),\s+(\d+),\s+(\d+),\s+(\d+),\s+(\d+)[,\s\d]*\)'
            for doc in currentDocs:
                lines += "db."+colName+".insert("+str(doc)+");\n".replace(" ","").replace(r'datetime\.datetime','new Date').replace('None','null')

        removeAndWriteFile("import_"+colName+".js", lines, "js")