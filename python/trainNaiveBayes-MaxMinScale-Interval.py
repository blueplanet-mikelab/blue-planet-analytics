import csv, pprint, json
import ssl, urllib.request
import os, datetime, re, copy
import math, random
import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB, BernoulliNB
import pymongo
import numpy as np
from math import sqrt, exp, pi
from utils.fileWritingUtil import removeAndWriteFile
from utils.measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore
from utils.naiveBayesUtil import dataPreparationToThreadsScores

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

with open('./config/database.json') as json_data_file:
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
    return [score < 1/3, score >= 1/3 and score < 2/3, score >= 2/3]
    

def initializeWordCount(threadsScores):
    wordCount = {}
    for thread in threadsScores:
        for word in thread['significant_words']:
            if word['key'] not in wordCount.keys():
                wordCount[word['key']] = []
    return wordCount


def createScoredModel(threadsScores, threadTheme):
    #! 5. calculate maxmin scale
    print("----------Naive Bayes-----------")
    minmaxScaleDict = initializeWordCount(threadsScores)
    selectedThread = []

    for idx, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        threadInput = { 'topic_id': topicID }
        currentThreadTheme = threadTheme[topicID] #['Mountain','Sea']
        print(idx,"--",topicID)
        if len(currentThreadTheme) > 1:
            continue
        
        selectedThread.append(topicID)
        #! word appear
        for word in thread['significant_words']:
            key = word['key']
            minmaxScaleDict[key].append(word['count'])

        #!! word_list has -> thread word not have
        for key, val in minmaxScaleDict.items():
            countLength = len(val)
            minmaxScaleDict[key].extend(np.zeros((idx+1)-countLength).tolist())
    
    removeAndWriteFile(dir_path+'5-0-selected-threads.json', minmaxScaleDict)
    removeAndWriteFile(dir_path+'5-1-count-before-maxmin.json', minmaxScaleDict)

    #! calculate maxmin-scale
    for key, countVal in minmaxScaleDict.items():
        scaler = MinMaxScaler()
        scaler.fit(np.array(countVal).reshape(-1,1))
        minmaxScaleDict[key] = scaler.transform([countVal]).tolist()[0]

    removeAndWriteFile(dir_path+'5-2-maxmin-scale.json', minmaxScaleDict)


    return minmaxScaleDict, selectedThread
    

def applyInterval(selectedThread, threadTheme, minmaxScaleDict):
    #! 5 Naive Bayes model - format inpit form
    print("----------Naive Bayes model - create interval model----------")
    #! Interval
    threadIntervalList = []
    for idx, topicID in enumerate(selectedThread):
        threadInput = { 'topic_id': topicID }
        currentThreadTheme = threadTheme[topicID] #['Mountain','Sea']
        print(idx,"--",topicID, currentThreadTheme)
        
        threadInterval = [ inte for score in minmaxScaleDict.values() for inte in selectInterval(score[idx])]
        threadInput['word_interval'] = threadInterval

        #!! add theme
        for idx, theme in enumerate(allThemeList):
            # print("current Theme:", theme)
            memberTheme = allThemeList[theme]
            if any([mt in currentThreadTheme for mt in memberTheme]):
                # print("append:",theme)
                threadInput['theme'] = theme
                threadIntervalList.append(threadInput)

    removeAndWriteFile(dir_path+'5-3-input-interval.json', threadIntervalList)
    return threadIntervalList
    
    #! insert model to mongo !FIXME error because exceed limit size of 16MB
    # model_col = db["naive_bayes_maxminscale"]
    # modelToInsert = [ 
    #     {'_id':key, 
    #     'topic_ids':themeDetail['topic_ids'], 
    #     'words_count':themeDetail['words_maxminscale']} 
    #     for key, themeDetail in themeModels.items()]
    # result = model_col.insert_many(modelToInsert)

def formatToXY(threadIntervalList=None):
    print("------formatToXY------")
    if threadIntervalList:
        with open(dir_path+'5-3-input-interval.json') as json_data_file:
            threadIntervalList = json.load(json_data_file) 
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
        Y.append(threadInput['theme'])
        X.append(threadInput['word_interval'])
    removeAndWriteFile(dir_path+'6-X.json', X)
    removeAndWriteFile(dir_path+'6-Y.json', Y)
    return X, Y

def importXY(dirX,dirY):
    print('importing X and Y')
    with open(dirX) as json_data_file:
        X = json.load(json_data_file) 
        print('finish import X')

    with open(dirY) as json_data_file:
        Y = json.load(json_data_file) 
        print('finish import Y')
    
    return X, Y

def createXYTestSet(threadScores, threadTheme):
    with open(dir_path+'5-1-count-before-maxmin.json') as json_data_file:
        countToMaxMin = json.load(json_data_file)
        # {
        #     'word1': [1,5,10,...],
        #     'word2': [...],
        #     ...
        # }
    X_test = []
    Y_test = []
    threadXDict = {}
    for thread in threadScores:
        currentThreadInterval = []
        threadWordList = { sw['key']:sw['count'] for sw in thread['significant_words'] }
        for key, val in countToMaxMin.items():
            if key in threadWordList:
                scaler = MinMaxScaler()
                scaler.fit(np.array(val).reshape(-1,1))
                count = threadWordList[key]
                sc = scaler.transform([[count]])[0][0]
                currentThreadInterval.extend(selectInterval(sc))
            else:
                currentThreadInterval.extend([True,False,False])
        threadXDict[thread['topic_id']] = X
        X_test.append(currentThreadInterval)
    
    removeAndWriteFile(dir_path+'test-threadX.json', threadXDict)    
    
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
    dir_path = './naiveBayes-maxminscale-interval/'
    # dir_path = './naiveBayes-maxminscale-oneTheme/'

    # threadsScores, threadTheme = dataPreparationToThreadsScores(dir_path, URLCONFIG['mike_thread'])
    
    print('------importing threadsScores and threadTheme-----')
    with open(dir_path+'4-cutThreadsScores.json') as json_data_file:
        threadsScores = json.load(json_data_file)
    with open(dir_path+'0-threadsTheme.json') as json_data_file:
        threadTheme = json.load(json_data_file)
    
    minmaxScaleDict, selectedThread = createScoredModel(threadsScores, threadTheme)
    threadIntervalList = applyInterval(selectedThread, threadTheme, minmaxScaleDict)
    X, Y = formatToXY(threadIntervalList)
    # X, Y = importXY(dir_path+'6-X.json',dir_path+'6-Y.json'):
    X_test, Y_test = createXYTestSet(threadsScores, threadTheme)

    print("-----start prediction")
    clf = BernoulliNB()
    clf.fit(X, Y)
    predictVal = clf.predict_proba(X_test)
    predictVal2 = clf.predict(X_test)
    print("-----predictVal-----")
    pprint.pprint(predictVal)
    removeAndWriteFile(dir_path+'test-prediction-result.json', predictVal.tolist())
    removeAndWriteFile(dir_path+'test-prediction-result2.json', predictVal2.tolist())


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