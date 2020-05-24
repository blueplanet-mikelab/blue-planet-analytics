# import pymongo
from pymongo import MongoClient, errors
import sys
sys.path.insert(0, '../utils')
import json
import time
from datetime import datetime, timedelta
import pprint
import urllib.request, ssl, requests
from manageContentUtil import cleanContent, fullTokenizationToWordSummary
from classification.classificationUtil import findCountries
from fileWritingUtil import removeAndWriteFile

with open('../config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

with open('../config/database.json') as json_data_file:
    DBCONFIG = json.load(json_data_file)
    dsdb = DBCONFIG["mikelab"]

with open('../utils/countriesListSorted.json','r', encoding="utf8") as json_file:
    countryList = json.load(json_file)
    for c in countryList:
        c["count"] = 0

PIPELINE = [
    { '$match': {
        "rooms":{'$in':["BP"] },
        "event":{'$in':["start"]},
        "tags": {'$nin':['วีซ่า', 'สายการบิน', 'ร้องทุกข์', 'เตือนภัย','ธนาคาร','ธุรกรรมทางการเงิน','เครื่องแต่งกาย', 'รถโดยสาร', 'โรงแรมรีสอร์ท', 'ค่ายเพลง', 'สนามบิน']}
    }},
    { '$addFields':{
        "topicIDNull": { '$ifNull': [ "$topic_id", False ] }
    }},
    { '$match': {
        "topicIDNull":{'$ne': False},
    }}
    # ,{ '$count': "passing_scores" }
]

#!TODO add pipeline
COUNTRYRANK_PIPELINE = []

def mongodb_connect():
    start_connection = time.time()
    try:
        client = MongoClient(dsdb["host"],27017,
                                    username=dsdb["username"],
                                    password=dsdb["password"],
                                    authSource=dsdb["authSource"],
                                    serverSelectionTimeoutMS = 2000)
        
        # client = MongoClient("localhost",27017,
        #                         authSource=dsdb["authSource"],
        #                         serverSelectionTimeoutMS = 2000)

        print("connection_status:",client)
        print("server_info():")
        pprint.pprint(client.server_info())
        return client
    except errors.ServerSelectionTimeoutError as err:
        print ("pymongo ERROR:", err)
        return None

    print("connection time:", time.time()-start_connection)

def getOneDayAgo():
    dateNow = datetime.now()
    date1DayAgo = dateNow - timedelta(days = 1)
    date1DayAgo = date1DayAgo.strftime("%Y%m%d")
    print('Return Date 1 day ago:', date1DayAgo)
    return date1DayAgo

def findEachThreadCountries(threadData):
    title = threadData['title']
    desc = threadData['desc']
    userID = threadData['uid']
    comments = [comment['desc'] for comment in threadData['comments'] if comment['uid']==userID]
    rawContent = title + desc + ' '.join(comments)
    
    tags = threadData["tags"]
    titleTokens, _ = fullTokenizationToWordSummary(cleanContent(title), maxGroupLength=3)
    descTokens, _ = fullTokenizationToWordSummary(cleanContent(desc + ' '.join(comments)), maxGroupLength=3)
    countries = findCountries(tags, titleTokens, descTokens) # array of string
    
    return countries

def checkTypeOfDocument(documents):
    selectedThreadList = []
    selectedTopicID = []
    countDict = {}
    for idx, doc in enumerate(documents):
        topicID = doc["topic_id"]
        print(idx, "-----", topicID)

        response = requests.get(URLCONFIG["mike_thread"]+topicID)
        if(bool(response.json()['found']) and topicID not in selectedTopicID):
            threadData = response.json()["_source"]
            if(threadData["type"] == 4 ):
                countries = findEachThreadCountries(threadData)
                selectedThreadList.append({
                    'topic_id': topicID,
                    'country_list': countries
                })

                #!SECTION count country
                for country in countries:
                    countryCode = country["country"]
                    countDict[countryCode] = 1 if countryCode not in countDict.keys() else countDict[countryCode] + 1

        # pprint.pprint(selectedThreadList)



        # if len(selectedThreadList)==10:
        #     break
    
    for country in countryList:
        thisCount = [num for cd, num in countDict.items() if cd == country["country"]]
        if len(thisCount) == 1:
            country["count"] = thisCount[0]

    return selectedThreadList



if __name__ == "__main__":
    test = cleanContent("test")

    # date1DayAgo = getOneDayAgo()
    date1DayAgo = '20200307'
    
    col_name = 'click-{}'.format(date1DayAgo)
    print(col_name)

    client = mongodb_connect()

    # dbs = client.list_database_names()
    # print(dbs)

    db = client[dsdb["click_db"]]
    clicksteam_col = db[col_name]
    # except AttributeError as error:
    #     # should raise AttributeError if mongodb_connect() function returned "None"
    #     print ("Get MongoDB database and collection ERROR:", error)

    print("query...")
    start = time.time() #!
    results = list(clicksteam_col.aggregate(PIPELINE))
    print("finish query")
    print("documents len:",len(results))
    print(time.time() - start) #!

    #! start classify country
    # selectedThreadList = checkTypeOfDocument(results)

    selectedThreadList = []
    selectedTopicID = []
    countDict = {}
    project_db = client[dsdb["db"]]
    selected_threads_col = project_db["selected_threads_"+date1DayAgo]
    skip = 97100
    for idx, doc in enumerate(results[skip:]):
        # if idx<18200:
        #     continue
        topicID = doc["topic_id"]
        print(idx+skip, "-----", topicID)

        response = requests.get(URLCONFIG["mike_thread"]+topicID)
        if(bool(response.json()['found']) and topicID not in selectedTopicID):
            threadData = response.json()["_source"]
            if(threadData["type"] == 4 ):
                countries = findEachThreadCountries(threadData)
                selectedThreadList.append({
                    'topic_id': topicID,
                    'country_list': countries
                })

                #!SECTION count country
                for country in countries:
                    countryCode = country["country"]
                    countDict[countryCode] = 1 if countryCode not in countDict.keys() else countDict[countryCode] + 1

        if (idx+1)%100==0 or (idx+1)==len(results):
            insert_result = selected_threads_col.insert_many(selectedThreadList)
            print("insert_result--",insert_result)
            selectedThreadList = []
        # pprint.pprint(selectedThreadList)

        # if len(selectedThreadList)==10:
        #     break
    
    # for country in countryList:
    #     thisCount = [num for cd, num in countDict.items() if cd == country["country"]]
    #     if len(thisCount) == 1:
    #         country["count"] = thisCount[0]

    # country_rank_col = project_db["country_rank_"+date1DayAgo]
    # insert_result = country_rank_col.insert_many(countryList)
    # removeAndWriteFile("./"+"country_rank_"+date1DayAgo+".json", countryList)

    #! old
    # print(">>>>>selected documents len:", len(selectedThreadList))
    # pprint.pprint(selectedThreadList)
    # print(">>>>>country count:")
    # pprint.pprint([cl for cl in countryList if cl["count"]>0])

    # project_db = client[dsdb["db"]]
    # country_rank_col = project_db["country_rank_"+date1DayAgo]
    # result = country_rank_col.insert_many(countryList)
    # print("result--",result)
    # removeAndWriteFile("./"+"country_rank_"+date1DayAgo+".json", countryList)


    


