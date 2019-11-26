import csv
import pprint
import urllib.request, json 
from pythainlp.tokenize import word_tokenize
import pythainlp.corpus as pycorpus
import re
import math
import pymongo
import os
import datetime

from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import cleanContent, getStopWords

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

if __name__ == "__main__":
    with open('./config/database.json') as json_data_file:
        dbConfig = json.load(json_data_file)
    client = pymongo.MongoClient(dbConfig["host"],
                                27017,
                                username=dbConfig["username"],
                                password=dbConfig["password"],
                                authSource=dbConfig["authSource"] )
    db = client[dbConfig["db"]]

    #! 0. read csv -> threadsList
    with open('./labeledThreadsbyHand.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        removeAndWriteFile('0-threads100.json', threadsList)

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

        #! 1. retrieve title+destription+comment
        title = threadData['_source']['title']
        desc = threadData['_source']['desc']
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID]
        rawContent = title + desc + ' '.join(comments)

        #! 2. tokenize+wordsummary
        tokens = word_tokenize(cleanContent(rawContent), engine='attacut-sc')
        wordsSum, tokensLength, wordSumDict = createWordsSummary(tokens, getStopWords(addMore=True))
        # freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength, "created_at":datetime.datetime.now()})
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength})


    #! 3. push to mongo   
    # wordsum_col = db["word_summary"]
    # result = wordsum_col.insert_many(freqDictList)
    # print("result--",result)
    removeAndWriteFile('1-wordsummary.json', freqDictList)

    #! 4. TFIDF calculation
    threadsScores = calculateFullTFIDF(freqDictList) # consists of TF, IDF, and TFIDF scores
    removeAndWriteFile('3-threadsScores.json', threadsScores)
    
    # for tfidfThread in threadsScores:
    #     tfidfDict = tfidfThread['tfidf_scores']
    #     if len(tfidfDict) > 100:
    #         for key, score in list(tfidfDict.items()):
    #             # print(key, ":", score)
    #             if score < 0.0035 or score > 0.02:
    #                 # print("del:", key)
    #                 del tfidfDict[key]
    #         tfidfThread['tfidf_scores'] = { k : v for k, v in sorted(tfidfDict.items(), key=lambda x: x[1], reverse=True)}
    # removeAndWriteFile('3-threadsScores-valcut.json', threadsScores)

    #! 4.2 cut off some keys using tfidf by scores
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

            thread['tfidf_scores'] = tscoresList
    removeAndWriteFile('3-threadsScores-percent.json', threadsScores)

    # result = tfidf_col.insert_many(threadsScores)
    # print("result--",result)

    #! 5.0 Vector calculation
    # print("----------vector creation-----------")
    # dfScoresfname = "4-keysDFScores.json"
    # if os.path.isfile(dfScoresfname):
    #     with open('./'+dfScoresfname,'r', encoding="utf8") as json_file:
    #         dfScoresDict = json.load(json_file)
    # else:
    #     dfScoresDict = computeDF(threadsScores, fname=dfScoresfname)
    
    #! 5.1 Theme selection and word counting
    themesVector = []
    # at least 1 theme and no more than 4 per thread -> only count more than 5 per theme
    for i, thread in enumerate(threadsList):
        topicID = thread["TopicID"]
        threadKeys = [[score['key'] for score in scores["scores"]] for scores in threadsScores if scores["topic_id"]==topicID][0]
        
        threadsThemeList = thread["Theme"].replace(" ","").split(",") #string
        for idx, theme in enumerate(threadsThemeList):
            if not [vec for vec in themesVector if vec['type']==theme]: #create new theme
                themesVector.append({'type':theme, 'topic_ids':[], 'words_count':{}})
            
            for vector in themesVector: # select which theme to add
            # print("vector theme:",vector['type'])
                if vector['type'] == theme:
                    vector["topic_ids"].append(topicID)
                
                    for word in threadKeys:
                        vector['words_count'][word] = 1 if word not in vector['words_count'].keys() else vector['words_count'][word] + 1
                    
                    break # there is only one theme vector per theme
    #     # break # 1 thread
    removeAndWriteFile('4-themesVector_count.json',themesVector,'json')

    #! 5.2 Calculation TF, DF, vector value
    for vector in themesVector:
        sortedCount = {k:v for k, v in sorted(vector["words_count"].items(), key=lambda x: x[1], reverse=True)}
        wordsLength = len(vector["words_count"])
        topicsLength = len(vector["topic_ids"])
        themeName = vector['type']
        wordsVectors = []
        for key, count in sortedCount.items():
            tf = float(count/wordsLength)
            df = float(count/topicsLength)
            wordsVectors.append({
                'key':key,
                'tf': tf,
                'df': df,
                'vector': tf+df
            })
        vector["words_vectors"] = wordsVectors # already sort
    
    removeAndWriteFile('5-themesVector_success.json',themesVector,'json')

    #! 5.3 Sorted
    # for vector in themesVector:
    #     print("----theme:", vector['type'])
    #     print("before sorted:", len(vector["word_vectors"]))
    #     
    #     print("after sorted:", len(vector["word_vectors"]))
    #     # vector["created_at"] = datetime.datetime.now()
   
    # fname = '4-sortedThemesVector.json'
    # removeAndWriteFile(fname,themesVector,'json')

    colName = "vector_theme_v2"
    vector_col = db[colName]
    vector_col.drop()
    result = vector_col.insert_many(themesVector)
    print(result)

    lines = ""
    for vector in themesVector:
        lines += "db."+colName+".insert("+str(vector)+");\n".replace(" ","")

    removeAndWriteFile("./mongo_js/import_vectors_v2.js", lines, "js")
    


