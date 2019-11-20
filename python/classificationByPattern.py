import pymongo
from pprint import pprint
import re
import datetime
from enum import Enum 
import json, urllib.request
import math

from utils.manageContentUtil import firstClean
from utils.classificationUtil import findMonth, findCountries, calculateBudget

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

# get country list to classify country and find top country
with open('./countriesListSorted.json','r', encoding="utf8") as json_file:
    COUNTRYLIST = json.load(json_file)   

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
def findDuration(content):
    # print("------------Duration")
    # keywords = [
    #     "ตลอดระยะเวลา",
    # ]
    # TODO

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

        # digit before keyword
        while i >= foundIndex + currentIndex - 10 and i >= 0 :
            s = content[i: currentIndex + foundIndex].replace(" ","")
            # print("s -> ",s)
            if (i >= foundIndex - 4 and s.isdigit()): numBefore = int(s)
            elif s in numTH: numBefore = numTH.index(s) + 1
            elif s in numEng: numBefore = numEng.index(s) + 1
            elif numBefore != 0: break
            i -= 1

        if numBefore > 0: 
            if searchResult.group() == 'คืน': numBefore += 1 #3คืน duration must be 4-6days
            duration = chooseDuration(numBefore)
            # print('d from num before:',duration)
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
    if (duration["label"] == Duration.NOT_DEFINE): #numBefore still equal 0
        duration = chooseDuration(numAfter)
        # print('d from num after:',duration)

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
    diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(createdTime)
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
    content = firstClean(rawContent)
    spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    content = re.sub(spechar, ' ', content) #17 remove special character
    
    countries = findCountries(threadData["tags"], COUNTRYLIST, content) # array of countries
    duration = findDuration(content)
    days = duration["days"]
    budget = calculateBudget(countries, days)
    month = findMonth(content) # array of month with count
    totalView = 100000 #TODO
    totalPoint = threadData["point"]
    totalComment = threadData["comment_count"]
    
    return {
        "topic_id": threadData["tid"],
        "title": threadData["title"],
        "thumbnail": findThumbnail(threadData["desc_full"]+ ' '.join(comments)),
        "countries": countries,
        "duration": duration,
        "month": month,
        "season": findSeason(month,countries),
        "theme": ["Photography"], #TODO using Naive Bayes
        "budget": budget,
        "totalView": totalView,
        "totalPoint": totalPoint,
        "totalComment": totalComment,
        "popularity": calculatePopularity(totalView,totalPoint,totalComment,threadData["created_time"]), #TODO totoalView
        "created_at": threadData["created_time"]
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
    thread_col = db["threadCollection"]

    #TODO get topicID
    topicList = []
    totalThread = len(topicList)

    # loop each topic
    preposTopics = []
    for idx, topicID in enumerate(topicList):
        print(idx, "current topic_id:", topicID)
        
        with urllib.request.urlopen(URLCONFIG["mike_thread"] + topicID) as url:
            thread = json.loads(url.read().decode())
            threadData = thread["_source"]
        
        # skip visa topic
        if 'วีซ่า' in threadData['tags']:
            continue

        preposTopic = createPreprocessData(threadData) # get 1 forum as a document
        preposTopics.append(preposTopic)
        # print("------------------------------------------------------------")

        # push every 100 documents to database 
        if (idx+1)%1000 == 0 or (idx+1)==totalThread:
            result = thread_col.insert_many(preposTopics)
            print("result--",result)
            preposTopics = []
        
        # if idx > 100:
        #     break