import pymongo
from pprint import pprint
import re
from datetime import datetime, timedelta
import json, requests
import time

from utils.fileWritingUtil import removeAndWriteFile
from utils.preprocessDataUtil import createPreprocessData

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

def classifyByPttern():
    # today = 20200425
    # print("Today to query:", today)

    with open('./config/database.json') as json_data_file:
        DBCONFIG = json.load(json_data_file)
    dbDetail = DBCONFIG["mikelab"]
    client = pymongo.MongoClient(dbDetail["host"],
                                27017,
                                username=dbDetail["username"],
                                password=dbDetail["password"] )
    db = client[dbDetail["db"]]
    # print("collections list",db.list_collection_names())
    # print('thread_col:',dbDetail["threadcollection"])

    print("getting topicID start...", datetime.now())
    start = time.time() #!

    #!get topicID
    db_click = client[dbDetail['click_db']]
    date2DayAgo = datetime.strftime(datetime.now() - timedelta(2), '%Y%m%d')
    thread_col = db[str(dbDetail["threadcollection"])+"_{}".format(date2DayAgo)]
    print("Date2DayAgo to query:", date2DayAgo)
    # date2DayAgo = today - 2
    col_name = 'click-{}'.format(str(date2DayAgo))
    click_col = db_click[col_name]
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
        }},
        { '$group': {
            '_id': "$topic_id",
            'view': {'$sum': 1}
        }}
        ,{ '$sort' : { 'view' : -1 } }
        # ,{ '$count': "passing_scores" }
    ]
    topicList = list(click_col.aggregate(PIPELINE))
    totalThread = len(topicList)
    print('topic list length:',totalThread)
    # viewCount = {}

    print('get topicID use:',time.time() - start) #!
    
    print("prepare view weekly start...", datetime.now())
    start = time.time() #!
    #!prepare view weekly
    weeklyView = {}
    for i in range(2,8):
        # dateStr = datetime.strftime(datetime.now() - timedelta(i), '%Y%m%d')
        dateStr = today - i
        print(dateStr)
        col = db_click['click-{}'.format(str(dateStr))]
        vieww = list(col.aggregate(PIPELINE))
        viewwDict = { topic['_id']:topic['view'] for topic in vieww }
        weeklyView[dateStr] = viewwDict
        # print(weeklyView[dateStr])
        # print('----------------------------')
        # print(viewwDict)
        # print(dateStr, vieww, weeklyView)
    print('prepare view weekly use:',time.time() - start) #!

    print("looping thread start...", datetime.now())
    start = time.time() #!
    #!loop each topic
    preposTopics = []
    for idx, topic in enumerate(topicList):
        # if idx < 12700:
        #     continue
        
        topicID = topic['_id']
        print(idx, "current topic_id:", topicID)
        
        response = requests.get(URLCONFIG["mike_thread"]+topicID)
        if(bool(response.json()['found'])):
            threadData = response.json()["_source"]
        
        # skip visa topic (done in finding topicID)
        # skipTags = ['วีซ่า', 'สายการบิน', 'ร้องทุกข์', 'เตือนภัย','ธนาคาร','ธุรกรรมทางการเงิน','เครื่องแต่งกาย', "รถโดยสาร", "โรงแรมรีสอร์ท", "ค่ายเพลง", "สนามบิน"]
        # if  len([tag for tag in threadData['tags'] for skipTag in skipTags if tag.find(skipTag)!=-1]) > 0:
        #     continue
        
        if(threadData["type"] == 4 ):
            print('yes')
            totalView = topic['view']
            for day, viewDict in weeklyView.items():
                totalView = totalView + viewDict[topicID] if topicID in viewDict else 0
                # print(day, viewDict[topicID] if topicID in viewDict else 0, totalView)
            
            threadData['view'] = totalView

            preposTopic = createPreprocessData(threadData) # get 1 forum as a document
            if preposTopic == None: # countries null them skip
                continue
        
            preposTopics.append(preposTopic)
            # pprint(preposTopic)
            print('finish')
            # break
            # result = thread_col.insert_many(preposTopics)
            # print("result--",result)
            # preposTopics = []
        
        # print("------------------------------------------------------------")
        
        # push every 100 documents to database 
        if (idx+1)%100 == 0 or (idx+1)==totalThread:
            result = thread_col.insert_many(preposTopics)
            print("result--",result)
            preposTopics = []
        
        # break
    
    print('finish looping:',time.time() - start) #!

if __name__ == "__main__":
    classifyByPttern()