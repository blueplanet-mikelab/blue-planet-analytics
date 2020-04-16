import pymongo
from pprint import pprint
import re
from datetime import datetime, timedelta
from enum import Enum 
import json, urllib.request, requests
import math
import time

from utils.manageContentUtil import firstClean, cleanContent, fullTokenizationToWordSummary
from utils.classificationUtil import findMonth, findCountries, calculateBudget, findThemeByKeyWord, findBudgetByPattern
from utils.fileWritingUtil import removeAndWriteFile

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

class Duration:
    NOT_DEFINE = "Not Define" #type 0
    ONEDAY      = "1 Day" #type 1
    TWODAYS     = "2 Days" #type 2
    THREEDAYS   = "3 Days" #type 3
    FOURDAYS    = "4 Days" #type 4
    FIVEDAYS    = "5 Days" #type 5
    SIXDAYS     = "6 Days" #type 6
    SEVENDAYS   = "7 Days" #type 7
    EIGHTDAYS   = "8 Days" #type 8
    NINEDAYS    = "9 Days" #type 9
    TENDAYS     = "10 Days" #type 10
    ELEVENDAYS  = "11 Days" #type 11
    TWELVEDAYS  = "12 Days" #type 12
    MORE = "More than 12 Days" #type 13

thaiDigit = [
        {"thaiDigit": "หนึ่ง" , "val":1},
        {"thaiDigit": "สอง" , "val":2},
        {"thaiDigit": "สาม" , "val":3},
        {"thaiDigit": "สี่" , "val":4},
        {"thaiDigit": "ห้า" , "val":5},
        {"thaiDigit": "หก" , "val":6},
        {"thaiDigit": "เจ็ด" , "val":7},
        {"thaiDigit": "แปด" , "val":8},
        {"thaiDigit": "เก้า" , "val":9}
    ]

numEng = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eigth', 'nine', 'ten', 'eleven', 'twelve', 'thirteen']
numTH = ['หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า', 'สิบ', 'สิบเอ็ด', 'สิบสอง', 'สิบสาม']

def chooseDuration(num):
    duration = { "days": 0, "label": Duration.NOT_DEFINE }
    if (num == 1): duration = { "days": 1, "label": Duration.ONEDAY }
    elif (num > 1 and num <= 12): duration = { "days": num, "label": "{} Days".format(num) }
    elif (num > 12): duration = { "days": num, "label": Duration.MORE }
    return duration

"""
- วันที่สอง 2 ไม่ได้ตามด้วยเดือน
- แบบ 3 วัน 2 คืน หรือ 4 วัน 3 คืน (เลือกเอาอันที่มากที่สุด)
- คืน (ไม่มีคำว่า วัน)
- Day 1, day 2
TODO - เดินทางตั้งแต่ 28/3/2559 ถึง 1/4/2559
@params content all content from topic's owner including comments
"""
def findDuration(content,tags):
    # print("------------Duration")
    # keywords = [
    #     "ตลอดระยะเวลา",
    # ]
    # TODO

    if "One Day Trip" in tags:
        return { "days": 1, "label": Duration.ONEDAY }

    duration = { "days": 0, "label": Duration.NOT_DEFINE }
    numAfter = 0
    numBefore = 0

    foundIndex = 0
    currentIndex = 0
    while (duration["label"] == Duration.NOT_DEFINE and foundIndex != -1 and currentIndex < len(content)):
        # print(foundIndex, currentIndex)
        # print(content[currentIndex:])
        searchResult = re.search(r'วัน|day|คืน',content[currentIndex:])
        if searchResult != None: foundIndex = searchResult.start()
        else: break
        # print("match idx",foundIndex, "-> ",content[foundIndex:foundIndex+10])
        i = currentIndex + foundIndex - 1
        # print(searchResult.start(), searchResult.group())

        # include one day pass
        num = 0
        while i >= foundIndex + currentIndex - 10 and i >= 0 :
            if num != 0: 
                numBefore = num if num > numBefore else numBefore
                break
            
            # print("s -> ",s)
            s = content[i: currentIndex + foundIndex].replace(" ","")
            if (i >= foundIndex - 4 and s.isdigit()): num = int(s)
            elif s in numTH: num = numTH.index(s) + 1
            elif s in numEng: num = numEng.index(s) + 1
            
            i -= 1

        if numBefore > 0 and (searchResult.group() == 'คืน' or searchResult.group() == 'วัน'): 
            numBefore = numBefore + 1 if searchResult.group() == 'คืน' else numBefore  #3คืน duration must be 4-6days
            duration = chooseDuration(numBefore)
            break

        isWanTee = searchResult.group() == 'วัน' and content[searchResult.end():searchResult.end()+3] == 'ที่' #เจอ วันที่
        if ((searchResult.group() == 'day') or  isWanTee) and numBefore == 0: # check more of day 1, day 2, .... only 'day' word
            i = foundIndex + 3 if not isWanTee else foundIndex + 6
            s = content[i:i+10].replace(" ","") #check only 10 characters after 'day'
            n = re.findall(r'[0-9]+',s)
            if len(n) > 0: 
                maxx = int(max(re.findall(r'[0-9]+',s)))
                if numAfter < maxx: numAfter = maxx
            # keep only max numAfter to declear duration

        currentIndex += foundIndex + 3
    
    #complete find วัน|day|คืน - check Do it has to use numAfter or not, numbefore has higher priority
    if (duration["label"] == Duration.NOT_DEFINE): #case: numBefore+Day and numAfter
        numMax = numBefore if numBefore > numAfter else numAfter
        duration = chooseDuration(numMax)

    return duration


"""
TODO find season from matching month and countries, add result of matching
@params month of topic's owner travelled
        countries of topic's owner travelled
"""
def findSeason(month, countries):
    return ""

"""
@params totalView a number of view of the forum
        totalVote a number of votes for the forum
        totalComment a number of comment on the forum
        createdDate
"""
def calculatePopularity(totalView,totalVote,totalComment,createdTime):
    diff = datetime.now() - datetime.fromtimestamp(createdTime)
    diffDays = diff.days + diff.seconds/60/60/24

    return (totalView+totalVote+totalComment) / diffDays

"""
#TODO
@params content with HTML tags to find ing tag
"""
def findThumbnail(rawContent):
    return ""

"""
Create a preprocessing document for each topic
@params totalView a number of view of the forum
        totalVote a number of votes for the forum
        totalComment a number of comment on the forum
        createdDate date of create the forum
"""
def createPreprocessData(threadData):
    title = threadData['title']
    desc = threadData['desc']
    userID = threadData['uid']
    comments = [comment['desc'] for comment in threadData['comments'] if comment['uid']==userID]
    rawContent = title + desc + ' '.join(comments)
    
    tags = threadData["tags"]
    titleTokens, _ = fullTokenizationToWordSummary(cleanContent(title), maxGroupLength=3)
    descTokens, _ = fullTokenizationToWordSummary(cleanContent(desc + ' '.join(comments)), maxGroupLength=3)
    countries = findCountries(tags, titleTokens, descTokens) # array of string
    if len(countries) == 0:
        return None

    content = firstClean(rawContent)
    spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    content = re.sub(spechar, ' ', content) #17 remove special character
    
    duration = findDuration(content, tags)
    days = duration["days"]
    budget = findBudgetByPattern(content)
    if budget == -1:
        calculateBudget(countries, days)
    month = findMonth(content) # array of month with count
    
    totalView = threadData['view']
    totalPoint = threadData["point"]
    totalComment = threadData["comment_count"]
    
    return {
        "topic_id": threadData["tid"],
        "title": title,
        "short_desc": desc[:250],
        "thumbnail": findThumbnail(threadData["desc_full"]+ ' '.join(comments)) if "desc_full" in threadData else None, 
        "countries": countries,
        "duration": duration,
        "month": month,
        "season": findSeason(month,countries),
        "theme": findThemeByKeyWord(content,tags), #TODO using Naive Bayes
        "budget": budget,
        "total_view": totalView,
        "total_point": totalPoint,
        "total_comment": totalComment,
        "popularity": calculatePopularity(totalView,totalPoint,totalComment,int(threadData["created_time"])),
        "created_at": threadData["created_time"],
        "doc_created_at": datetime.now()
    }

if __name__ == "__main__":
    with open('./config/database.json') as json_data_file:
        DBCONFIG = json.load(json_data_file)
    dbDetail = DBCONFIG["mikelab"]
    client = pymongo.MongoClient(dbDetail["host"],
                                27017,
                                username=dbDetail["username"],
                                password=dbDetail["password"] )
    db = client[dbDetail["db"]]
    # print("collections list",db.list_collection_names())
    thread_col = db[dbDetail["threadcollection"]]
    # print('thread_col:',dbDetail["threadcollection"])

    print("getting topicID start...", datetime.now())
    start = time.time() #!

    #!get topicID
    db_click = client[dbDetail['click_db']]
    date1DayAgo = datetime.strftime(datetime.now() - timedelta(1), '%Y%m%d')
    col_name = 'click-{}'.format(date1DayAgo)
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
        dateStr = datetime.strftime(datetime.now() - timedelta(i), '%Y%m%d')
        print(dateStr)
        col = db_click['click-{}'.format(dateStr)]
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
            # viewCount[topicID] = 1 if topicID not in viewCount else viewCount[topicID] + 1
            totalView = topic['view']
            for day, viewDict in weeklyView.items():
                totalView = totalView + viewDict[topicID] if topicID in viewDict else 0
                # print(day, viewDict[topicID] if topicID in viewDict else 0, totalView)
            
            threadData['view'] = totalView

            preposTopic = createPreprocessData(threadData) # get 1 forum as a document
            if preposTopic == None: # countries null them skip
                continue
        
            preposTopics.append(preposTopic)
        else:
            continue
        # print("------------------------------------------------------------")
        
        # push every 100 documents to database 
        if (idx+1)%100 == 0 or (idx+1)==totalThread:
            result = thread_col.insert_many(preposTopics)
            print("result--",result)
            preposTopics = []
        
        # if idx > 100:
        #     break
    
    print('finish looping:',time.time() - start) #!