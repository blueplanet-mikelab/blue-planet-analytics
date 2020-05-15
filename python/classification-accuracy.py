import pymongo
from pprint import pprint
import re
from datetime import datetime, timedelta
import json, requests
import time
import csv

from utils.fileWritingUtil import removeAndWriteFile
from utils.preprocessDataUtil import createPreprocessData
from utils.naiveBayesUtil import computeJaccardSimilarityScore

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

if __name__ == "__main__":

    with open('./config/database.json') as json_data_file:
        DBCONFIG = json.load(json_data_file)
    dbDetail = DBCONFIG["mikelab"]
    client = pymongo.MongoClient(dbDetail["host"],
                                27017,
                                username=dbDetail["username"],
                                password=dbDetail["password"] )
    db = client[dbDetail["db"]]
    thread_col = db["classified_thread_300"]

    #! 0. read csv -> threadsList
    print('----------Import data from mike-----------')
    with open('labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
        # removeAndWriteFile('0-300threads.json', threadsList)
        # removeAndWriteFile('0-threadsTheme.json', threadTheme)

    #!loop each topic
    # preposTopics = []
    # totalThread = len(threadsList)
    # for idx, topic in enumerate(threadsList):
        
    #     topicID = topic['TopicID']
    #     print(idx, "current topic_id:", topicID)
        
    #     response = requests.get(URLCONFIG["mike_thread"]+topicID)
    #     if(bool(response.json()['found'])):
    #         # print("---topic found")
    #         threadData = response.json()["_source"]
        
    #         # skip visa topic (done in finding topicID)
    #         # skipTags = ['วีซ่า', 'สายการบิน', 'ร้องทุกข์', 'เตือนภัย','ธนาคาร','ธุรกรรมทางการเงิน','เครื่องแต่งกาย', "รถโดยสาร", "โรงแรมรีสอร์ท", "ค่ายเพลง", "สนามบิน"]
    #         # if  len([tag for tag in threadData['tags'] for skipTag in skipTags if tag.find(skipTag)!=-1]) > 0:
    #         #     continue
           
    #         threadData['view'] = 10000

    #         preposTopic = createPreprocessData(threadData) # get 1 forum as a document
    #         if preposTopic == None: # countries null them skip
    #             print("None")
    #             preposTopics.append({
    #                 "topic_id": topicID,
    #                 "countries": None
    #             })
    #         else:
    #             preposTopics.append(preposTopic)
    #         # print('finish')
    #         # push every 100 documents to database 
    #         if (idx+1)%10 == 0 or (idx+1)==totalThread:
    #             # pprint(preposTopics)
    #             result = thread_col.insert_many(preposTopics)
    #             print("result--",result)
    #             preposTopics = []
        
    print("finish - preprocess data")
    classifiedThread300 = list(thread_col.find())
    p = re.compile('[a-zA-Z]+')
    accuracyThreads = []
    for clasThread in classifiedThread300:
        print("----------------------------------")
        topicID = str(clasThread["topic_id"])
        byhandThread = {}
        for thread in threadsList:
            if topicID == thread['TopicID']:
                byhandThread = {
                    "topic_id": topicID,
                    "countries": [re.search(r'[ก-๙]+', thread['Country']).group()],
                    "duration": thread['Duration'],
                    "theme": thread['Theme'].replace(" ","").split(','),
                    "budget": float(re.search(r'[0-9\.\-]+', thread['Budget']).group())
                }
                break
        
        accuracy = {
            "topic_id": topicID
        }
        # Country
        print("---countries--")
        clasCountries = [country["nameThai"][0] for country in clasThread["countries"]] if clasThread["countries"] != None else []
        print("clasCountries:", clasCountries)
        print("byhandThread:", byhandThread["countries"])
        accuracy["countryJC"] = {
            "classified": clasCountries,
            "byhandThread": byhandThread["countries"],
            "checked":computeJaccardSimilarityScore(clasCountries,byhandThread["countries"])
        }
        # Duration
        print("---duration--")
        clasDuration = clasThread["duration"]["label"] if "duration" in clasThread else ""
        print("clasDuration:", clasDuration)
        print("byhandThread:", byhandThread["duration"])
        accuracy["duration"] = {
            "classified": clasDuration,
            "byhandThread": byhandThread["duration"],
            "checked": clasDuration in byhandThread["duration"]
        }
        # Theme
        print("---theme--")
        clasTheme = [tm["theme"] for tm in clasThread["theme"]] if "theme" in clasThread else []
        print("clasTheme:", clasTheme)
        print("byhandThread:", byhandThread["theme"])
        accuracy["themeJC"] = {
            "classified": clasTheme,
            "byhandThread": byhandThread["theme"],
            "checked": computeJaccardSimilarityScore(clasTheme,byhandThread["theme"])
        }
        # Budget
        print("---budget--")
        if "budget" in clasThread and clasThread["budget"] != None:
            clasBudget = clasThread["budget"]
        elif "budget" in clasThread and clasThread["budget"] == None:
            clasBudget = -1.0
        else:
            clasBudget = 0.0
        print("clasBudget:", clasBudget)
        print("byhandThread:", byhandThread["budget"])
        accuracy["budget"] = {
            "classified": clasBudget,
            "byhandThread": byhandThread["budget"],
            "checked": byhandThread["budget"] == clasBudget
        }

        accuracyThreads.append(accuracy)
        pprint(accuracy)

    removeAndWriteFile("checked_300threads.json", accuracyThreads)

    countryAcc = [ th["countryJC"]["checked"] for th in accuracyThreads]
    durationAcc = { "true": 0, "false": 0 }
    for th in accuracyThreads:
        if th["duration"]["checked"]:
            durationAcc["true"] += 1
        else:
            durationAcc["false"] += 1
    themeAcc = [ th["themeJC"]["checked"] for th in accuracyThreads]
    budgetAcc = { "true": 0, "false": 0 }
    for th in accuracyThreads:
        if th["budget"]["checked"]:
            budgetAcc["true"] += 1
        else:
            budgetAcc["false"] += 1
    
    accCount = {
        "countryJC": sum(countryAcc)/len(countryAcc),
        "duration": durationAcc,
        "themeJC": sum(themeAcc)/len(themeAcc),
        "budget": budgetAcc
    }


    removeAndWriteFile("accuracy_300threads.json", accCount)