import csv, pprint, json
import ssl, urllib.request
import os, datetime, re, copy
import math, random
from math import sqrt, exp, pi
import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB, BernoulliNB
import pymongo
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, '../utils')
from fileWritingUtil import removeAndWriteFile
from measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore
from naiveBayesUtil import dataPreparationToThreadsScores, cutoffKeys, computeJaccardSimilarityScore, toThreadsScores

with open('../config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

with open('../config/database.json') as json_data_file:
    DBCONFIG = json.load(json_data_file)
    dsdb = DBCONFIG["mikelab"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]

allThemeList = {
    'Mountain':['Mountain','Waterfall'], 
    'Sea':['Sea'], 
    'Religion':['Religion'], 
    'Historical':['Historical'], 
    'Entertainment':['Museum','Zoo','Amusement','Aquariam','Casino','Adventure'], 
    # 'Festival':['Festival','Exhibition'], 
    'Eating':['Eating'],
    # 'NightLifeStyle':['NightFood', 'Pub', 'Bar'], 
    'Photography':['Photography'],
    'Sightseeing':['Sightseeing']
}

def selectInterval(score):
    return [score == 0, score > 0 and score < 1/3, score >= 1/3 and score < 2/3, score >= 2/3]

def applyInterval(threadsScores, minmaxScaleDict, dataType, dirPath):
    #! 5 Naive Bayes model - format inpit form
    print("----------Naive Bayes model - create interval model----------")
    #! Interval
    threadIntervalList = []
    countInterval = {}
    for idx, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        threadInput = { 'topic_id': topicID }
        currentThreadTheme = thread["theme"] #['Mountain','Sea']
        print(idx,"<-->",topicID, currentThreadTheme)
        
        countInterval[topicID] = [0,0,0,0]
        threadInterval = [ interval for score in minmaxScaleDict.values() for interval in selectInterval(score[idx])]
        for score in minmaxScaleDict.values():
            interval = selectInterval(score[idx])
            trueIndex = interval.index(True)
            countInterval[topicID][trueIndex] += 1
        
        threadInput['word_interval'] = threadInterval
        threadInput['theme'] = currentThreadTheme
        
        threadIntervalList.append(threadInput)

    removeAndWriteFile(dirPath+'5-3-'+dataType+'-oneTheme-interval.json', threadIntervalList)
    removeAndWriteFile(dirPath+'5-4-'+dataType+'-count-interval.json', countInterval)
    return threadIntervalList

# create list of words of all documents
def initializeWordCount(threadsScores):
    print("------initializeWordCount-----")
    wordCount = {}
    for thread in threadsScores:
        for word in thread['significant_words']:
            if word['key'] not in wordCount.keys():
                wordCount[word['key']] = []
    return wordCount

def createScoredModel(threadsScores, minmaxScaleDict, dataType, dirPath):
    #! 5. calculate maxmin scale
    print("----------Naive Bayes-----------")
    for idx, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        print(idx,"<->",topicID)
        
        #! word appear
        for word in thread['significant_words']:
            key = word['key']
            if key in minmaxScaleDict:
                minmaxScaleDict[key].append(word['count'])
                # print(key, minmaxScaleDict[key])

        #!! word_list has -> thread word not have
        for key, val in minmaxScaleDict.items():
            countLength = len(val)
            # print(idx, key, countLength, (idx+1)-countLength)
            minmaxScaleDict[key].extend(np.zeros((idx+1)-countLength).tolist())

    removeAndWriteFile(dirPath+'5-1-'+dataType+'-count-before-maxmin.json', minmaxScaleDict)

    #! calculate maxmin-scale
    for key, countVal in minmaxScaleDict.items():
        scaler = MinMaxScaler()
        scaler.fit(np.array(countVal).reshape(-1,1))
        minmaxScaleDict[key] = scaler.transform([countVal]).tolist()[0] #value of maxmin-scale of each word
    
    removeAndWriteFile(dirPath+'5-2-'+dataType+'-maxmin-scale.json', minmaxScaleDict)
    if 'train' in dataType:
        removeAndWriteFile(dirPath+'5-0-'+dataType+'-oneTheme-words.json', list(minmaxScaleDict.keys()))

    threadIntervalList = applyInterval(threadsScores, minmaxScaleDict, dataType, dirPath)

    return threadIntervalList

# fit trained data to X, Y
def formatToXY(threadIntervalList, dataType, dirPath):
    print("------formatToXY------")
    # threadIntervalList <= 
    # [{
    #     'topic_ids':[...],
    #     'word_interval':[True,False,...],
    #     'theme':["Mountain"]
    #   },...
    # ]

    # create model
    X = []
    Y = []
    p = re.compile('[a-zA-Z]+')
    currentTheme = str(p.match(dirPath).group())
    print("fit XY current theme:",currentTheme)
    
    for threadInput in threadIntervalList:
        X.append(threadInput['word_interval'])
        # Theme: tain=>keep theme string, test=>keep in list of theme
        if dataType == "train" and threadInput['theme'][0] == currentTheme: #only 1 theme
            Y.append('Yes')
        elif dataType == "train" and threadInput['theme'][0] != currentTheme: #only 1 theme
            Y.append('No')
        else:
            Y.append(selectMajorTheme(threadInput['theme']))

    removeAndWriteFile(dirPath+'6-X_'+dataType+'.json', X)
    removeAndWriteFile(dirPath+'6-Y_'+dataType+'.json', Y)
    return X, Y

# import X, Y from file
def importXY(dirX,dirY):
    # print('importing', dirX, 'and', dirY)
    with open(dirX) as json_data_file:
        X = json.load(json_data_file) 
        print('finish import', dirX)

    with open(dirY) as json_data_file:
        Y = json.load(json_data_file) 
        print('finish import', dirY)
    
    return X, Y

def createXYTestSet(cdir, testData_threadScores, threadTheme):
    print("----createXYTestSet-----")
    with open(cdir+'merge-5-0-train-oneTheme-words.json') as modelWords_file:
        modelWords = json.load(modelWords_file)
        minmaxScaleDict = {key: list() for key in modelWords}
    testIntervalList = createScoredModel(testData_threadScores, minmaxScaleDict, dirPath=cdir, dataType='test')
    X_test, Y_test = formatToXY(testIntervalList, dataType='test', dirPath=cdir)
    
    return X_test, Y_test

def prediction(X,Y,X_test,Y_test, distribution, created=None):
    if distribution=='GUS':
        clf = GaussianNB()
        distribution_name = "GaussianNB"
    elif distribution=='MNB':
        clf = MultinomialNB()
        distribution_name = "MultinomialNB"
    elif distribution=='CNB':
        clf = ComplementNB()
        distribution_name = "ComplementNB"
    elif distribution=='BERN':
        clf = BernoulliNB()
        distribution_name = "BernoulliNB"
    else:
        print("Invalid distribution code")
        return None

    print("-----creating", distribution, "model")
    clf.fit(X, Y)
    print("-----start",distribution,"prediction")
    predictVal = clf.predict(X_test)
    clf_acc = accuracy(Y_test, predictVal)
    clf_recall = recallScore(Y_test, predictVal)
    clf_precision = precisionScore(Y_test, predictVal)
    # clf_confusion_matrix = confusionMatrix(Y_test, predictVal)
    
    return {
            "distribution": distribution_name,
            "predict_val": predictVal.tolist(),
            "actual_val": Y_test,
            'accuracy': clf_acc,
            'recall_score': clf_recall,
            'precision_score': clf_precision,
            # 'confusion_matrix': clf_confusion_matrix
            'created_time': created
        }


def selectMajorTheme(themeList):
    majorTheme = themeList.copy()
    for idx, theme in enumerate(themeList):
        if theme not in allThemeList.keys():
            for major, memberList in allThemeList.items():
                if themeList in memberList:
                    majorTheme[idx] = major
                    break
    return majorTheme


if __name__ == "__main__":

    #! 0. read csv -> threadsList
    # print('----------Import data from mike-----------')
    # with open('../labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
    #     threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    #     threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
    #     removeAndWriteFile('0-300threads.json', threadsList)
    #     removeAndWriteFile('0-threadsTheme.json', threadTheme)
    
    #! 0 alternative
    with open('0-300threads.json') as thread_list_file:
        threadsList = json.load(thread_list_file)
    with open('0-threadsTheme.json') as thread_theme_file:
        threadTheme = json.load(thread_theme_file)

    #! 1 create list of topicID seperated by theme
    # topicIdListbyTheme = {}
    # for tid,themeList in threadTheme.items():
    #     if len(themeList) == 1:
    #         oneTheme = selectMajorTheme(themeList[0])
    #         if oneTheme not in topicIdListbyTheme:
    #             topicIdListbyTheme[oneTheme] = []
    #         topicIdListbyTheme[oneTheme].append(tid)
        
    # removeAndWriteFile('0-topicID_oneTheme.json', topicIdListbyTheme)
    
    #! 1 alternative
    with open('0-topicID_oneTheme.json') as onetheme_file:
        topicIdListbyTheme = json.load(onetheme_file)

    #! 2 Create threadScores -> loop of each one theme
    # print("----create model-----")
    # oneThemeIntervalDict = {}
    # for theme, tidlist in topicIdListbyTheme.items():
    #     cdir = theme+"-idf-new/"
    #     Path("./"+cdir).mkdir(exist_ok=True)
    #     print(theme,"------",cdir)

    #     #! 2-1 current theme - YES
    #     oneThemeList = [thread for thread in threadsList if thread["TopicID"] in tidlist]
    #     oneThemeThreadScores = toThreadsScores('./'+cdir, URLCONFIG['mike_thread'], oneThemeList, cutOffBy='idf')
        
    #     # add theme in to thread
    #     for threadscore in oneThemeThreadScores:
    #         threadscore["theme"] = threadTheme[threadscore["topic_id"]]
        
    #     #! 2-2 other theme - NO
    #     otherThemeTopicID = [ ]
    #     for tm, tidlist in topicIdListbyTheme.items():
    #         if tm != theme:
    #             otherThemeTopicID.extend(tidlist)
    #     otherThemeList = [thread for thread in threadsList if thread["TopicID"] in otherThemeTopicID]
    #     # print(otherThemeList)
    #     otherdir = './'+cdir+'other-'
    #     otherThemeThreadScores = toThreadsScores(otherdir, URLCONFIG['mike_thread'], otherThemeList, cutOffBy=None)

    #     # add theme in to thread
    #     for threadscore in otherThemeThreadScores:
    #         threadscore["theme"] = threadTheme[threadscore["topic_id"]]
        
    #     #! 2-2 merge Yes and No
    #     minmaxScaleDict = initializeWordCount(oneThemeThreadScores)
    #     mergedThreadScores = oneThemeThreadScores + otherThemeThreadScores
    #     threadInterval = createScoredModel(mergedThreadScores, minmaxScaleDict, dataType='train', dirPath=cdir+'merge-')
        
    #     #! finish
    #     oneThemeIntervalDict[theme] = threadInterval
    #     removeAndWriteFile(cdir+'5-5-merge_interval.json', threadInterval)

    # removeAndWriteFile('merge-5-5-allOneTheme-interval.json', oneThemeIntervalDict)
    
    #! 2 alternative
    #! select IDF
    with open('./merge-5-5-allOneTheme-interval.json') as model_file:
        oneThemeIntervalDict = json.load(model_file)

    #! 3-4 NB+prob
    #! 3-0 create threadScore of all threads without cut-off 
    # print("-----Create testData_threadScores-----")
    # Path("./test_data_tfidf").mkdir(exist_ok=True)
    # testData_threadScores = toThreadsScores("test_data_tfidf/", URLCONFIG['mike_thread'], threadsList, cutOffBy=None)   
    #! 3-0 alternative
    with open('./test_data_tfidf/4-uncutThreadsScores.json') as model_file:
        testData_threadScores = json.load(model_file)
    
    predictResult = {}
    topicIdList = []
    # add theme, initial resultdict, topicid order list
    for threadscore in testData_threadScores:
        threadscore["theme"] = threadTheme[threadscore["topic_id"]]
        predictResult[str(threadscore["topic_id"])] = []
        topicIdList.append(str(threadscore["topic_id"]))
    
    # Prodiction using NB model of each theme
    for theme, threadIntervalList in oneThemeIntervalDict.items():
        cdir = theme+"-idf-new/"
        #! 3 Fit X, Y, Create X_test, Y_test
        # print("-----Fit X, Y, Create X_test, Y_test-----")
        # X, Y = formatToXY(threadIntervalList, dataType='train', dirPath=cdir)
        # X_test, Y_test = createXYTestSet(cdir, testData_threadScores, threadTheme)
        
        #! 3 alternative
        print(theme, "import success---------------")
        X, Y = importXY(cdir+'6-X_train.json',cdir+'6-Y_train.json')
        X_test, Y_test = importXY(cdir+'6-X_test.json',cdir+'6-Y_test.json')

        #!4 prediction using BernoulliNB with proba only
        print("-----start prediction")
        clf = BernoulliNB()
        clf.fit(X, Y)
        predictValProba = clf.predict_proba(X_test).tolist()
        predictVal = clf.predict(X_test).tolist()
        # print("-----predictVal-----")
        # pprint.pprint(predictValProba)
        # print("=====================")
        # pprint.pprint(predictVal)
        countDict = {}
        for val in predictVal:
            countDict[val] = 1 if val not in countDict else countDict[val] + 1
        pprint.pprint(countDict)

        removeAndWriteFile(cdir+'7-predic-proba-2.json', predictValProba)
        removeAndWriteFile(cdir+'7-predic-val-2.json', predictVal)
        
        for idx, topicId in enumerate(topicIdList):
            if predictVal[idx] == 'Yes':
                predictResult[topicId].append(theme)
            # elif predictVal[idx] == 'No' -> done nothing

    removeAndWriteFile('8-complete-predict-result-2.json', predictResult)


    #!5 Jaccard
    jaccardScores = {}
    with open('8-complete-predict-result-2.json') as predictResult_file:
        predictResult = json.load(predictResult_file)
    for tid, predictedThemeList in predictResult.items():
        actualTheme = selectMajorTheme(threadTheme[tid])
        jaccard = computeJaccardSimilarityScore(predictedThemeList, actualTheme)
        jaccardScores[tid] = {
            "actual_theme": actualTheme,
            "predict_theme": predictedThemeList,
            "jaccard_score": jaccard
        }

    removeAndWriteFile('9-jaccard-scores-2.json', jaccardScores)

    # find accuracy
    jcscores = [val["jaccard_score"] for tid, val in jaccardScores.items()]
    avg = sum(jcscores) / len(jcscores)
    print("Average:",avg)
    

    #!------------------------------------------------------
    # csvData = "Distribution, Accuracy, Recall, Precision\n"

    # X_test = X.copy()
    # Y_test = Y.copy()
    # result_col = db["naive_bayes_result"]

    # modelResult = []
    # created_time = datetime.datetime.now()

    # GUS_result = prediction(X,Y,X_test,Y_test,distribution='GUS', created=created_time)
    # modelResult.append(GUS_result)
    # # csvData += "{},{},{},{}".format(GUS_result['distribution'],GUS_result['accuracy'],GUS_result['recall_score'],GUS_result['precision_score'])
    
    # MNB_result = prediction(X,Y,X_test,Y_test,distribution='MNB', created=created_time)
    # modelResult.append(MNB_result)
    # # csvData += "{},{},{},{}".format(MNB_result['distribution'],MNB_result['accuracy'],MNB_result['recall_score'],MNB_result['precision_score'])
    
    # CNB_result = prediction(X,Y,X_test,Y_test,distribution='CNB', created=created_time)
    # modelResult.append(CNB_result)
    # # csvData += "{},{},{},{}".format(CNB_result['distribution'],CNB_result['accuracy'],CNB_result['recall_score'],CNB_result['precision_score'])

    # BERN_result = prediction(X,Y,X_test,Y_test,distribution='BERN', created=created_time)
    # modelResult.append(BERN_result)
    # csvData += "{},{},{},{}".format(BERN_result['distribution'],BERN_result['accuracy'],BERN_result['recall_score'],BERN_result['precision_score'])
    
    # removeAndWriteFile(dirPath+'7-prediction-result.json', modelResult)
    # removeAndWriteFile(dirPath+'7-prediction-comparison.csv', csvData, 'csv')
    
    # To mongo
    # print("----->insert")
    # insert_result = result_col.insert_many(modelResult)
    # print(insert_result)