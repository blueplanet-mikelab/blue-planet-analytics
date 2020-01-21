import csv, pprint, json
import ssl, urllib.request
import os, datetime, re
import math
from sklearn.preprocessing import MinMaxScaler
import pymongo
import numpy as np
from math import sqrt, exp, pi
from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import fullTokenizationToWordSummary

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

dir_path = './naiveBayes-maxminscale/'

def selectInterval(score):
    return {
        'I1': score >= 0 and score < 1/3,
        'I2': score >= 1/3 and score < 2/3,
        'I3': score >= 2/3 and score <= 1
    }

if __name__ == "__main__":
    with open('./config/database.json') as json_data_file:
        dbConfig = json.load(json_data_file)
    dsdb = dbConfig["mikelab"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]

    #! 0. read csv -> threadsList
    with open('./labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
        removeAndWriteFile(dir_path+'0-300threads.json', threadsList)

    print("----------Word Summary-----------")
    freqDictList = []
    threadsCount = len(threadsList)
    for idx, thread in enumerate(threadsList):
        topicID = thread['TopicID']
        print(idx,"--",topicID)
        
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(URLCONFIG["mike_thread"]+topicID, context=context) as url:
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
        tokens, wordSumDict = fullTokenizationToWordSummary(rawContent, maxGroupLength=3, addCustomDict=True)
        tokensLength = sum([count for k,count in wordSumDict.items()])
        wordsSumArray = []
        for k,v in wordSumDict.items():
            wordsSumArray.append({'word': k, 'count': v})
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSumArray, "tokens_length": tokensLength})
        
        # if idx==3:
        #     break


    #! 1-3. push to mongo / save to json  
    removeAndWriteFile(dir_path+'1-wordsummary.json', freqDictList)

    #! 2,3. calculate IDF and TFIDF calculation
    threadsScores = calculateFullTFIDF(freqDictList, dir_path+'2-IDFScoreByWord.json') # consists of TF, IDF, and TFIDF scores
    removeAndWriteFile(dir_path+'3-threadsScores.json', threadsScores)
    
    # scores to cut
    # if score < 0.0035 or score > 0.02:
    #     del tfidfDict[key]

    #! 4. cut off some keys using tfidf by scores
    for thread in threadsScores:
        tscoresList = thread['scores']
        if len(tscoresList) > 100: #cut words if that threads has more than 100 words
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
    removeAndWriteFile(dir_path+'4-cutThreadsScores.json', threadsScores)

    #! 5. Theme Counting as model input
    print("----------Naive Bayes-----------")
    allThemeList = {
        'Mountain':['Mountain'], 'Waterfall':['Waterfall'], 
        'Sea':['Sea'], 
        'Religion':['Religion'], 
        'Historical':['Historical'], 
        'Entertainment':['Museum','Zoo','Amusement','Aquariam','Casino','Adventure'], 
        'Festival':['Festival','Exhibition'], 
        'Eating':['Eating'],
        'NightLifeStyle':['NightFood', 'Pub', 'Bar'], 
        'Photography':['Photography'],
        'Sightseeing':['Sightseeing']
    }
    themeModels = {}
    for theme in allThemeList:
        themeModels[theme] = { 'topic_ids':[], 'words_count':{} , 'word_list':[] }
    # pprint.pprint(themeModels)
    
    for i, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        threadThemeList = threadTheme[topicID] #['Mountain','Sea']
        print(i,"--",topicID, threadThemeList)

        for idx, theme in enumerate(allThemeList):
            # print("current Theme:", theme)
            memberTheme = allThemeList[theme]
            #add topic id
            if any([mt in threadThemeList for mt in memberTheme]):
                # print("append:",theme)
                themeModels[theme]['topic_ids'].append(topicID)
            else:
                # print("skip")
                continue

            topicLength = len(themeModels[theme]['topic_ids'])
            wordNotInThread = themeModels[theme]['word_list'].copy()

            #add word_count and word_list
            for word in thread['significant_words']:
                key = word['key']
                #!! thread word has -> word_list not have
                if key not in themeModels[theme]['word_list']:
                    themeModels[theme]['word_list'].append(key)
                    themeModels[theme]['words_count'][key] = np.zeros(topicLength-1).tolist()
                else:
                    wordNotInThread.remove(key) #filter only word in word_list but not in wordThread
                
                themeModels[theme]['words_count'][key].append(word['count']) #have to done everytime
            
            #!! word_list has -> thread word not have
            for w in wordNotInThread:
                themeModels[theme]['words_count'][w].append(0)

    removeAndWriteFile(dir_path+'5-themeModels-onlycount.json', themeModels)
    
    #! 5 Naive Bayes model - apply MaxMinScale
    print("----------Naive Bayes model - apply MaxMinScale----------")
    for idx, theme in enumerate(themeModels):
        themeModels[theme]['words_maxminscale'] = {}
        themeModels[theme]['words_interval'] = {}
        for word, count in themeModels[theme]['words_count'].items():
            scaler = MinMaxScaler()
            count_ndarray = np.array(count).reshape(-1, 1)
            scaler.fit(count_ndarray)
            maxmin_score = scaler.transform(count_ndarray).reshape(1, -1).tolist()[0]
            themeModels[theme]['words_maxminscale'][word] = maxmin_score
            themeModels[theme]['words_interval'][word] = [selectInterval(sc) for sc in maxmin_score]
    # pprint.pprint(themeModels)
    removeAndWriteFile(dir_path+'5-themeModels-maxmin-interval.json', themeModels)