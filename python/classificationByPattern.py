import pymongo
from pprint import pprint
import re
import datetime
from enum import Enum 
import json 
import math

class Duration:
    NOT_DEFINE = "Not Define" #type 0
    ONETHREE = "1 to 3 Days" #type 1
    FOURSIX = "4 to 6 Days" #type 2
    SEVENNINE = "7 to 9 Days" #type 3
    TENTWELVE = "10 to 12 Days" #type 4
    MORE = "More than 12 Days" #type 5

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

"""
TODO not only tags but also content
- ไทย: ในประเทศ, all thai provinces//done
- ญป: โอซาก้า เกียวโต คันไซ
- อเมริกา: นิวยอร์ก
เอาเมืองใส่ตอนหาในแท๊กด้วย แต่ก็ต้องระวัง push ประเทศซ้ำ
@params tags array of tags
        countryList from json file
"""
def findCountries(tags, countryList, content):    
    # print("----------Country")
    foundList = []
    for tag in tags:
        for country in countryList:
            # skip if that country has already in the list
            if True in [country['country'] in found['country'] for found in foundList]:
                continue

            for thaiName in country['nameThai']:
                # print(tag,thaiName)
                if tag.find(thaiName) != -1 and country["country"] not in [c["country"] for c in foundList]:
                    # print("tag:",tag)
                    foundList.append(country)

    # if found list is not found -> search more in content
    if len(foundList) == 0:
        for country in countryList:
            for thaiName in country['nameThai']:
                if content.find(thaiName) != -1 and country["country"] not in [c["country"] for c in foundList]:
                    # print("content:",country["nameEnglish"])
                    foundList.append(country)
    
    if any("เที่ยวต่างประเทศ" in tag for tag in tags):
        foundList = [c for c in foundList if not (c["country"] == 'TH')]

    return foundList


def chooseDuration(num):
    duration = { "type": 0, "label": Duration.NOT_DEFINE }
    if (num > 0 and num <= 3): duration = { "type": 1, "label": Duration.ONETHREE }
    elif (num > 3 and num <= 6): duration = { "type": 2, "label": Duration.FOURSIX }
    elif (num > 6 and num <= 9): duration = { "type": 3, "label": Duration.SEVENNINE }
    elif (num > 9 and num <= 12): duration = { "type": 4, "label": Duration.TENTWELVE }
    elif (num > 12): duration = { "type": 5, "label": Duration.MORE }
    return duration

"""
TODO วันที่สอง 2 ไม่ได้ตามด้วยเดือน
- แบบ 3 วัน 2 คืน หรือ 4 วัน 3 คืน (เลือกเอาอันที่มากที่สุด)
- คืน (ไม่มีคำว่า วัน)
- เดินทางตั้งแต่ 28/3/2559 ถึง 1/4/2559
@params content all content from topic's owner including comments
"""
def findDuration(content):
    # print("------------Duration")
    # keywords = [
    #     "ตลอดระยะเวลา",
    # ]
    # TODO

    duration = { "type": 0, "label": Duration.NOT_DEFINE }
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

        if searchResult.group() == 'day' and numBefore == 0: # check more of day 1, day 2, .... only 'day' word
            i = foundIndex + 3
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
#TODO whole year
# หน้าหลังตัวย่อภาษาอังกฤษต้องไม่ใช่ตัวภาษาอังกฤษ
Finding a month that forum's owner travelled
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findMonth(content):
    # print("---------Month")
    # wholeYearKeywords = [
    #     "365วัน","1ปี"
    # ]


    monthKeywords = [
        ['มกรา', 'มค\\.', 'ม\\.ค', 'Jan', 'January',"ปีใหม่","นิวเยียร์"],
        ['กุมภา', 'กพ\\.', 'ก\\.พ', 'Feb', 'February',"เดือน2"],
        ['มีนา', 'มีค\\.', 'มี\\.ค', 'Mar', 'March',"เดือน3"],
        ['เมษา', 'เมย\\.', 'เม\\.ย', 'Apr', 'April',"เดือน4"],
        ['พฤษภา', 'พค\\.', 'พ\\.ค', 'May', 'May',"เดือน5"],
        ['มิถุนา', 'มิย\\.', 'มิ\\.ย', 'June', 'June',"เดือน6"],
        ['กรกฎา', 'กค\\.', 'ก\\.ค', 'July', 'July',"เดือน7"],
        ['สิงหา', 'สค\\.', 'ส\\.ค', 'Aug', 'August',"เดือน8"],
        ['กันยา', 'กย\\.', 'ก\\.ย', 'Sep', 'September',"เดือน9"],
        ['ตุลา', 'ตค\\.', 'ต\\.ค', 'Oct', 'October',"เดือน10"],
        ['พฤศจิกา', 'พย\\.', 'พ\\.ย', 'Nov', 'November',"เดือน11"],
        ['ธันวา', 'ธค\\.', 'ธ\\.ค', 'Dec', 'December',"เค้าท์ดาวน์","วันส่งท้ายปีเก่า","เดือน12"]
    ]

    monthCount = []
    for keyword in monthKeywords:
        rex = '|'.join(keyword)
        rex = r'' + rex
        # print(rex)
        # print("-->" )
        # pprint(re.findall(rex, content, re.IGNORECASE))
        matchs = []
        for match in re.compile(rex, re.IGNORECASE).finditer(content):
            i = match.start()
            word = match.group()
            # print(i,word)
            if word.lower() == keyword[3].lower() and (bool(re.search(r'[a-zA-Z]',content[i-1])) or bool(re.search(r'[a-zA-Z]',content[i+1]))):
                # print("skip---",word)
                continue
            matchs.append(word)

        monthCount.append({ "month": keyword[4], "count": len(matchs) })
    monthCount = sorted(monthCount, key = lambda i: (i['count'], i['month']), reverse=True) 
    # pprint(monthCount)
    return monthCount


"""
TODO find season from matching month and countries, add result of matching
@params month of topic's owner travelled
        countries of topic's owner travelled
"""
def findSeason(month, countries):
    return ""

"""
find theme from keywords (first only using test searching) 
TODO add more keywords
TODO using tags
TODO next use image analytic
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findTheme(content,tags):
    themeKeywords = [
        ['Entertainment', 'สวนสนุก', 'สวนสัตว์'],
        ['Water Activities', 'ทะเล', 'สวนน้ำ', 'สวนสยาม', 'ดำน้ำ', 'เล่นน้ำตก', 'ว่ายน้ำ', 'ล่องแก่ง'],
        ['Religion', 'ศาสนา', 'วัด',"สิ่งศักดิ์สิทธิ์","พระ","เณร"], # หน้าวัด ห้าม ห
        ['Mountain', 'เขา', 'ภู', 'เดินป่า',"camping","แคมป์","น้ำตก"], # start with ภู
        ['Backpack', 'แบกเป้', ' แบกกระเป๋า'], #ดูจาก tags
        ['Honeymoon', 'ฮันนีมูน',"โรแมนติก","คู่รัก","สวีท","เดท"],
        ['Photography', 'ภาพถ่าย', 'ถ่ายรูป','วิว','ถ่าย'],
        ['Eatting', 'อาหาร', 'ร้านอาหาร', 'ขนม', 'ของหวาน',"ร้านกาแฟ", "อร่อย", 'ชา', 'เครื่องดื่ม','ของกิน','รสชาติ', 'คาเฟ่'], # อาหาร แค่คำว่า match
        ['Event', 'งานวัด', 'งานกาชาด', 'เทศกาล', 'เฟสติวัล']
    ]

    text = content + ''.join(tags)
    themes = []
    for keyword in themeKeywords:
        rex = r'' + '|'.join(keyword)
        # print(rex)
        # รอบ regilion -> หน้าวัด ห้าม ห
        if "วัด" in keyword:
            match = []
            for m in re.compile(rex).finditer(text):
                if m.group == 'วัด':
                    if text[m.start()-1] != 'ห':
                        match.append(m.group())
                else:
                    match.append(m.group())
                # print(m.start(), m.group(), text[m.start()])
        # themes อื่นๆ
        else:
            match = re.findall(rex, text, re.IGNORECASE)
        # print(match)

        themes.append({ "theme": keyword[0], "count": len(match) })

    themes = sorted(themes, key = lambda i: (i['count'], i['theme']), reverse=True) 
    # pprint(monthCount)

    return themes

"""
TODO find budget using money words
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findBudget(content):
    # print("---------Budget")
    digitAfterWords = [
        "ด้วยเงิน","ราคารวม","ทั้งหมดรวม","รวมค่าเสียหาย","จบแค่","คนละ","งบจำกัด","รวม"
    ]
    digitBeforeWords = [
        "บาทต่อท่าน","ต่อคน","ต่อท่าน","บาท","บ.","บาท/คน"
    ]
    moneyWords = [
        {"key":"แสน", "val":100000},
        {"key":"หมื่น","val":10000},
        {"key":"พัน","val":1000},
        {"key":"ร้อย","val":100},
        {"key":"สิบ","val":10} 
        # คนละพันบาท
    ]
    candidate = []
    
    # 1. digi after words
    rex = r'' + '|'.join(digitAfterWords)
    # print(rex)
    for m in re.compile(rex).finditer(content):
        i = m.start() + 3 #3 is the minimun length of keyword
        # print(m.start(),m.group())

        number = "0"

        # คนละพันบาท
        # rex = r'' + '|'.join([ key["key"] for key in moneyWords])
        # result = re.findall(rex, content[i:i+10])
        # print("result:", result)
        # if len(result) > 0:
        #     number = [d["val"] for d in moneyWords if d["key"] == result[0]][0]
        #     candidate.append(int(number))
        #     continue
        # คนละสี่พัน คนละ4พัน ยังไม่สำเร็จ

        sum = 0
        while(i < len(content) and i < m.start()+50):
            # print(i,content[i])
            if content[i].isdigit():
                # 41000
                # print("if1")
                number += content[i]
            elif number != "0" and content[i] == ',':
                # print("if2")
                # 41,xxx
                if content[i+1] == 'x' or content[i+1] == '+':
                    number += "000"
                    i += 3
                    while(content[i+1] == 'x' or content[i+1] == '+'): # 4,xxxx xเกิน
                        i += 1
                # 41,000 ผ่าน , ไปทำตัวถัดไป
            elif number != "0" and (content[i] == '+' or content[i] == 'x'):
                # print("if3")
                # รวม 857+957+23
                if (content[i] == '+' and content[i+1] != '+'):
                    sum += int(number)
                    number = "0"
                # ราคา 8+++ หรือ 4xxx
                else:
                    n = content[i]
                    # find length of xx..x or ++..+
                    while(content[i] == content[i+1]):
                        n += content[i+1]
                        i += 1
                    # define +++ or xxx as 000
                    for i in range(len(n)): 
                        number += "0"
            elif number != "0" and not content[i].isdigit():
                # print("if4")
                if sum != 0:
                    sum += int(number)
                    candidate.append(sum)
                else:
                    candidate.append(int(number))
                break # candidate: [4000, 13, 6000, 500, 1, 197, 30, 7, 9423]
            i += 1
    # print("candidate:",candidate)

    # 2. digit before word
    # may be nost necessary

    # next step find the maximun price as approximate budget แต่ถ้าน้อยกว่า 100 ไม่นับ
    budget = -1
    for c in candidate:
        if c > 100 and c > budget:
            budget = c
    return budget


"""
TODO make decision of the formular
@params totalView a number of view of the forum
        totalVote a number of votes for the forum
        totalComment a number of comment on the forum
        createdDate
"""
def calculatePopularity(totalView,totalVote,totalComment,createdDate):
    # print("--------Popular calculation")
    # print("total:",totalView+totalVote+totalComment)
    diff = datetime.datetime.now() - topic['created_at']
    diffDays = diff.days + diff.seconds/60/60/24
    # print("diff days:",diffDays) # days ratio
    return (totalView+totalVote+totalComment) / diffDays

"""
Create a preprocessing document for each topic
@params totalView a number of view of the forum
        totalVote a number of votes for the forum
        totalComment a number of comment on the forum
        createdDate date of create the forum
"""
def createPreprocessData(topic, comments, countryList):
    content = topic["topic"] + ' ' +topic["msg_clean"] + ' ' + ' '.join([str(c["msg_clean"]) for c in comments])
    month = findMonth(content) # string
    countries = findCountries(topic["tags"], countryList, content) # array of string
    totalView = topic["stat"]["views"]
    totalVote = topic["stat"]["votes"]
    totalComment = topic["stat"]["comments"]
    
    return {
        "topic_id": topic["_id"],
        "title": topic["topic"],
        "thumbnail": topic["thumbnail"],
        "countries": countries,
        "duration": findDuration(content),
        "month": month,
        "season": findSeason(month,countries),
        "theme": findTheme(content,topic["tags"]),
        "budget": findBudget(content),
        # "budget": findBudget("คนละ 1000 คนละ 2,000 คนละ 3xxx คนละ 4+++ คนละ 5,xxx คนละ 6,+++ คนละ7พัน คนละพัน คนละเก้าพัน"),
        "totalView": totalView,
        "totalVote": totalVote,
        "totalComment": totalComment,
        "popularity": calculatePopularity(totalView,totalVote,totalComment,topic["created_at"]),
        "created_at": topic["created_at"]
    }

if __name__ == "__main__":
    with open('./config/database.json') as json_data_file:
        dbConfig = json.load(json_data_file)
    dsdb = dbConfig["pantip-ds"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]
    # print("collections list",db.list_collection_names())

    # get country list to classify country and find top country
    with open('./countriesListSorted.json','r', encoding="utf8") as json_file:
        countryList = json.load(json_file)

    # get topics from Pantip database
    collist = db.list_collection_names()
    if "review_topics" in collist:
        topics_col = db["review_topics"]
    totalDocs = topics_col.count_documents({})
    print('topics count:',totalDocs)

    # get comments from Pantip database
    if "review_comments" in collist:
        comments_col = db["review_comments"]
        print('comments count:',comments_col.count_documents({}))

    # if "classified_thread" in collist:
    #     classified_col = db["classified_thread"]
    #     classified_col.drop()

    # define collection for push
    # classified_col = db["classified_thread"]
    classified_col = db["classified_thread_221019"]
    classified_col.create_index("topic_id", unique = True)

    # loop each topic
    preposTopics = []
    for idx, topic in enumerate(topics_col.find({})):
        print(idx, "current topic_id:", topic["_id"])
        
        # skip visa topic
        if 'วีซ่า' in topic['tags']:
            continue
        
        topic_id = topic["_id"]
        comments = [comment for comment in comments_col.find({"topic_id": topic_id})]
        preposTopic = createPreprocessData(topic,comments,countryList) # get 1 forum as a document
        preposTopics.append(preposTopic)
        # print("------------------------------------------------------------")

        # push every 100 documents to database 
        if (idx+1)%1000 == 0 or (idx+1)==totalDocs:
            result = classified_col.insert_many(preposTopics)
            print("result--",result)
            preposTopics = []
        
        # if idx > 100:
        #     break