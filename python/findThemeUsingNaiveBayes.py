import csv
import pprint
import urllib.request, json 
from pythainlp.tokenize import word_tokenize
import re
import math
import pymongo
import os
import datetime
from math import sqrt, exp, pi
from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import cleanContent, getStopWords

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

# Calculate the mean of a list of numbers
def calMean(numbers, length):
	return sum(numbers)/length
 
# Calculate the standard deviation of a list of numbers
def calStdev(numbers, avg, length):
    if length == 1:
        return 0
    variance = sum([(x-avg)**2 for x in numbers]) / (length-1)
    return sqrt(variance)


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

    #! 0. read csv -> threadsList
    with open('./labeledThreadsbyHand.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        removeAndWriteFile('0-122threads-9themes.json', threadsList)

    print("----------Word Summary-----------")
    freqDictList = []
    # pprint.pprint(threads)
    # pprint.pprint(threads[0])
    threadsCount = len(threadsList)
    for idx, thread in enumerate(threadsList):
        topicID = thread['TopicID']
        print(idx,"--",topicID)
        
        with urllib.request.urlopen(URLCONFIG["mike_thread"]+topicID) as url:
            threadData = json.loads(url.read().decode())
            # print(threadData)

        #! 1-1. retrieve title+destription+comment
        title = threadData['_source']['title']
        desc = threadData['_source']['desc']
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID]
        rawContent = title + desc + ' '.join(comments)

        #! 1-2. tokenize+wordsummary
        rawContent = re.sub(r'<[^<]+/>|<[^<]+>|\\.{1}|&[^&]+;|\n|\r\n','', rawContent) # to msg_clean
        tokens = word_tokenize(cleanContent(rawContent), engine='attacut-sc')
        wordsSum, tokensLength, wordSumDict = createWordsSummary(tokens, getStopWords(addMore=True))
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength})


    #! 1-3. push to mongo / save to json  
    # wordsum_col = db["word_summary"]
    # result = wordsum_col.insert_many(freqDictList)
    # print("result--",result)
    removeAndWriteFile('1-wordsummary.json', freqDictList)

    #! 2. calculate IDF
    threadsScores = calculateFullTFIDF(freqDictList, '2-IDFScoreByWord.json') # consists of TF, IDF, and TFIDF scores
    #! 3. TFIDF calculation
    removeAndWriteFile('3-threadsScores.json', threadsScores)
    
    # scores to cut
    # if score < 0.0035 or score > 0.02:
    #     del tfidfDict[key]

    #! 4. cut off some keys using tfidf by scores
    for thread in threadsScores:
        tscoresList = thread['scores']
        if len(tscoresList) > 100:
            # headcut = int(0.1*len(sortedDict))
            headcut = 0
            tailcut = len(tscoresList) - int(0.46*len(tscoresList))
            prevVal = -1
            for idx, scores in enumerate(tscoresList):
                if prevVal == -1:
                    prevVal = scores['tfidf']

                if (idx < headcut or idx > tailcut) and scores['tfidf'] != prevVal:
                    tscoresList.remove(scores)
                else:
                    prevVal = scores['tfidf']

        thread['significant_words'] = tscoresList
    removeAndWriteFile('4-cutThreadsScores.json', threadsScores)

    # result = tfidf_col.insert_many(threadsScores)
    # print("result--",result)

    #! 5.0 Theme model using Naive Bayes
    print("----------Naive Bayes-----------")
    allThemeList = ['Mountain', 'Entertainment', 'Photography', 'Eating', 'WaterActivities', 'Religion', 'Honeymoon', 'Backpack', 'Event']
    allWordList = []
    themeModels = {
        'Mountain':     {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Entertainment':{   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Photography':  {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Eating':       {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'WaterActivities':{ 'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Religion':     {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Honeymoon':    {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Backpack':     {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     },
        'Event':        {   'yes':{'topic_ids':[], 'words_count':{}},   'no':{'topic_ids':[], 'words_count':{}}     }

    }
    for i, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        print(i,"--",topicID)
        threadTheme = [t["Theme"] for t in threadsList if t["TopicID"]==topicID][0]
        threadThemeList = threadTheme.replace(" ","").split(",") #string
        
        for idx, theme in enumerate(allThemeList):
            isTheme = 'yes' if theme in threadThemeList else 'no'
            #add topic id
            themeModels[theme][isTheme]['topic_ids'].append(topicID)
            #add word
            # print(threadsScores['significant_words'])
            # print(type(threadsScores['significant_words']))
            for word in thread['significant_words']:
                key = word['key']
                if key not in allWordList:
                    allWordList.append(key)
                if key not in themeModels[theme][isTheme]['words_count'].keys():
                    themeModels[theme][isTheme]['words_count'][key] = []
                themeModels[theme][isTheme]['words_count'][key].append(word['count'])
    
    removeAndWriteFile('5-themeModels-onlycount.json', themeModels)
    removeAndWriteFile('5-allwordList.json', allWordList)
    
    #! 5.1 Find mean and stdev of each word in each class
    for idx, theme in enumerate(themeModels):
        for classTheme in themeModels[theme]:
            print(theme,"----", classTheme)
            length = len(themeModels[theme][classTheme]["topic_ids"])
            for word, numbers in themeModels[theme][classTheme]["words_count"].items():
                mean = calMean(numbers, length)
                themeModels[theme][classTheme]["words_count"][word] = {
                    "mean": mean,
                    "stdev": calStdev(numbers, mean, length),
                    "length":length
                }

    removeAndWriteFile('5-themeModels-finish.json', themeModels)