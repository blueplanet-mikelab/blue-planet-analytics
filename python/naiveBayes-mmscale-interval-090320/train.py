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
sys.path.insert(0, '../utils')
from fileWritingUtil import removeAndWriteFile
from measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore
from naiveBayesUtil import dataPreparationToThreadsScores, cutoffKeys, computeJaccardSimilarityScore

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

def selectInterval(score):
    return [score == 0, score > 0 and score < 1/3, score >= 1/3 and score < 2/3, score >= 2/3]

def applyInterval(threadsScores, threadTheme, minmaxScaleDict, dataType):
    #! 5 Naive Bayes model - format inpit form
    print("----------Naive Bayes model - create interval model----------")
    #! Interval
    threadIntervalList = []
    countInterval = {}
    for idx, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        threadInput = { 'topic_id': topicID }
        currentThreadTheme = threadTheme[topicID] #['Mountain','Sea']
        print(idx,"<-->",topicID, currentThreadTheme)
        
        countInterval[topicID] = [0,0,0,0]
        threadInterval = [ interval for score in minmaxScaleDict.values() for interval in selectInterval(score[idx])]
        for score in minmaxScaleDict.values():
            interval = selectInterval(score[idx])
            trueIndex = interval.index(True)
            countInterval[topicID][trueIndex] += 1
        
        threadInput['word_interval'] = threadInterval

        #!! add theme
        threadInput['theme'] = []
        for idx, theme in enumerate(allThemeList):
            # print("current Theme:", theme)
            memberTheme = allThemeList[theme]
            if any([mt in currentThreadTheme for mt in memberTheme]):
                # print("append:",theme)
                threadInput['theme'].append(theme)
        
        threadIntervalList.append(threadInput)

    removeAndWriteFile('5-3-'+dataType+'-oneTheme-interval.json', threadIntervalList)
    removeAndWriteFile('5-4-'+dataType+'-count-interval.json', countInterval)
    return threadIntervalList
    
    #! insert model to mongo !FIXME error because exceed limit size of 16MB
    # model_col = db["naive_bayes_maxminscale"]
    # modelToInsert = [ 
    #     {'_id':key, 
    #     'topic_ids':themeDetail['topic_ids'], 
    #     'words_count':themeDetail['words_maxminscale']} 
    #     for key, themeDetail in themeModels.items()]
    # result = model_col.insert_many(modelToInsert)

# create list of words of all documents
def initializeWordCount(threadsScores):
    wordCount = {}
    for thread in threadsScores:
        for word in thread['significant_words']:
            if word['key'] not in wordCount.keys():
                wordCount[word['key']] = []
    return wordCount

def createScoredModel(threadsScores, threadTheme, dataType):
    #! 5. calculate maxmin scale
    print("----------Naive Bayes-----------")
    if dataType == 'train': #oneTheme
        minmaxScaleDict = initializeWordCount(threadsScores)
    else: #test
        with open('./5-0-train-oneTheme-words.json') as oneThemeWords_file:
            oneThemeWords = json.load(oneThemeWords_file)
            minmaxScaleDict = {key: list() for key in oneThemeWords}
            # print(minmaxScaleDict)

    for idx, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        currentThreadTheme = threadTheme[topicID] #['Mountain','Sea']
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
    
    removeAndWriteFile('5-1-'+dataType+'-count-before-maxmin.json', minmaxScaleDict)

    #! calculate maxmin-scale
    for key, countVal in minmaxScaleDict.items():
        scaler = MinMaxScaler()
        scaler.fit(np.array(countVal).reshape(-1,1))
        minmaxScaleDict[key] = scaler.transform([countVal]).tolist()[0] #value of maxmin-scale of each word
    
    removeAndWriteFile('5-2-'+dataType+'-maxmin-scale.json', minmaxScaleDict)
    if dataType=='train':
        removeAndWriteFile('5-0-'+dataType+'-oneTheme-words.json', list(minmaxScaleDict.keys()))

    threadIntervalList = applyInterval(threadsScores, threadTheme, minmaxScaleDict, dataType)

    return threadIntervalList

# fit trained data to X, Y
def formatToXY(threadIntervalList, dataType):
    print("------formatToXY------")
    # [{
    #     'topic_ids':[...],
    #     'word_interval':[True,False,...],
    #     'theme':"Mountain"
    #   },...
    # ]

    # create model
    X = []
    Y = []
    for threadInput in threadIntervalList:
        Y.append(threadInput['theme'] if dataType != 'train' else threadInput['theme'][0]) # tain=>keep string, test=>keep array of string
        X.append(threadInput['word_interval'])

    if dataType == 'train':
        removeAndWriteFile('6-X.json', X)
        removeAndWriteFile('6-Y.json', Y)
    return X, Y

# import X, Y from file
def importXY(dirX,dirY):
    print('importing', dirX, 'and', dirY)
    with open(dirX) as json_data_file:
        X = json.load(json_data_file) 
        print('finish import', dirX)

    with open(dirY) as json_data_file:
        Y = json.load(json_data_file) 
        print('finish import', dirY)
    
    return X, Y

def createXYTestSet(threadScores, threadTheme):   
    allThreadIntervalList = createScoredModel(threadScores, threadTheme, dataType='test')
    X_test, Y_test = formatToXY(allThreadIntervalList, dataType='test')

    removeAndWriteFile('6-X_test.json', X_test)
    removeAndWriteFile('6-Y_test.json', Y_test)
    
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

if __name__ == "__main__":

    #! 1
    # threadsScores, threadTheme = dataPreparationToThreadsScores('./', URLCONFIG['mike_thread'])
   
    # testing cutting
    # with open('./3-threadsScores.json') as threadsScores_file:
    #     threadsScores_old = json.load(threadsScores_file)
    #     print("scores:",len(threadsScores_old[0]["scores"]))
    #     threadsScores = cutoffKeys('./', threadsScores_old.copy())

    #! 1 alternative
    print('------importing threadsScores and threadTheme-----')
    with open('./4-cutThreadsScores.json') as threadsScores_file:
        threadsScores = json.load(threadsScores_file)
    with open('./0-threadsTheme.json') as threadTheme_file:
        threadTheme = json.load(threadTheme_file)

    #! 2
    oneThemeThreads = [thread for thread in threadsScores if len(threadTheme[thread["topic_id"]]) == 1]
    removeAndWriteFile('5-0-oneTheme-threads.json', oneThemeThreads)
    oneThemeIntervalList = createScoredModel(oneThemeThreads, threadTheme, dataType='train')
    #! 2 alternative
    # with open('./5-3-oneTheme-interval.json') as model_file:
    #     oneThemeIntervalList = json.load(model_file)

    #! 3
    X, Y = formatToXY(oneThemeIntervalList, dataType='train')
    X_test, Y_test = createXYTestSet(threadsScores, threadTheme)
    #! 3 alternative
    # X, Y = importXY('6-X.json','6-Y.json')
    # X_test, Y_test = importXY('6-X_test.json','6-Y_test.json')

    #!4 prediction using BernoulliNB
    print("-----start prediction")
    clf = BernoulliNB()
    clf.fit(X, Y)
    predictValProba = clf.predict_proba(X_test).tolist()
    predictVal = clf.predict(X_test).tolist()
    print("-----predictVal-----")
    # pprint.pprint(predictValProba)
    removeAndWriteFile('7-prediction-probaResult.json', predictValProba)
    removeAndWriteFile('7-prediction-result.json', predictVal)
    
    # labels = clf.classes_
    # print("Labels:",labels)
    # predictResultFromProba = []
    # for proba in predictValProba:
    #     result = [labels[idx] for idx, num in enumerate(proba) if num > 0] #! all that > 0
    #     predictResultFromProba.append(result)

    # removeAndWriteFile('7-prediction-result-fromProba.json', predictResultFromProba)

    #!5 TODO Jaccard
    # jaccardScores = []
    # for i in range(len(Y_test)):
    #     jaccardScores.append(computeJaccardSimilarityScore[i], Y_test[i])

    # removeAndWriteFile('8-jaccard-fromProba-Y_test.json', predictResultFromProba)

    # correct = 0
    # for idx, predict in enumerate(predictVal):
    #     if predict in Y_test[idx]:
    #         correct += 1

    # print(correct)
    # print(len(Y_test), len(predictVal))
    # print(correct / len(Y_test) * 100)

    

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
    
    # removeAndWriteFile(dir_path+'7-prediction-result.json', modelResult)
    # removeAndWriteFile(dir_path+'7-prediction-comparison.csv', csvData, 'csv')
    
    # To mongo
    # print("----->insert")
    # insert_result = result_col.insert_many(modelResult)
    # print(insert_result)