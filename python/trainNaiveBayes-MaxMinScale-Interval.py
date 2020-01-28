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

def selectInterval(score):
    return score >= 0 and score < 1/3, score >= 1/3 and score < 2/3, score >= 2/3 and score <= 1
    

def initializeWordCount(threadsScores):
    wordCount = {}
    for thread in threadsScores:
        for word in thread['significant_words']:
            if word['key'] not in wordCount.keys():
                wordCount[word['key']] = []
    return wordCount


def createModel(threadsScores):
    #! 5. calculate maxmin scale
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

    #! calculate maxmin-scale
    for key, countVal in minmaxScaleDict:
        scaler = MinMaxScaler()
        scaler.fit(np.array(countVal).reshape(-1,1))
        minmaxScaleDict[key] = scaler.transform([countVal]).tolist()[0]

    removeAndWriteFile(dir_path+'5-maxmin-scale.json', minmaxScaleDict)
    
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

    removeAndWriteFile(dir_path+'5-input-interval.json', threadIntervalList)
    
    #! insert model to mongo !FIXME error because exceed limit size of 16MB
    # model_col = db["naive_bayes_maxminscale"]
    # modelToInsert = [ 
    #     {'_id':key, 
    #     'topic_ids':themeDetail['topic_ids'], 
    #     'words_count':themeDetail['words_maxminscale']} 
    #     for key, themeDetail in themeModels.items()]
    # result = model_col.insert_many(modelToInsert)

def importXY():
    with open(dir_path+'5-input-interval.json') as json_data_file:
        print('read data')
        threadIntervalList = json.load(json_data_file) 
        # [{
        #     'topic_ids':[...],
        #     'word_interval':[True,False,...],
        #     'theme':"Mountain"
        #   },...
        # ]
        print('finish reading data')

    # create model
    X = []
    Y = []
    for threadInput in threadIntervalList:
        Y.append(threadInput['theme'])
        X.append(threadInput['word_interval'])
    removeAndWriteFile(dir_path+'6-X.json', X)
    removeAndWriteFile(dir_path+'6-Y.json', Y)
    return X, Y

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

    threadsScores = dataPreparationToThreadsScores(dir_path, URLCONFIG['mike_thread'])
    createModel(threadsScores)
    X, Y = importXY()

    # print('importing X and Y')
    # with open(dir_path+'6-X.json') as json_data_file:
    #     X = json.load(json_data_file) 
    #     print('finish import X')

    # with open(dir_path+'6-Y.json') as json_data_file:
    #     Y = json.load(json_data_file) 
    #     print('finish import Y')

    csvData = "Distribution, Accuracy, Recall, Precision\n"
    # ranint = random.sample(range(303), 30)
    # X_test = [X[i] for i in ranint]
    # Y_test = [Y[j] for j in ranint]
    X_test = X.copy()
    Y_test = Y.copy()
    result_col = db["naive_bayes_result"]

    for i in range(3):
        modelResult = []
        created_time = datetime.datetime.now()

        GUS_result = prediction(X,Y,X_test,Y_test,distribution='GUS', created=created_time)
        modelResult.append(GUS_result)
        csvData += "{},{},{},{}".format(GUS_result['distribution'],GUS_result['accuracy'],GUS_result['recall_score'],GUS_result['precision_score'])
        
        MNB_result = prediction(X,Y,X_test,Y_test,distribution='MNB', created=created_time)
        modelResult.append(MNB_result)
        csvData += "{},{},{},{}".format(MNB_result['distribution'],MNB_result['accuracy'],MNB_result['recall_score'],MNB_result['precision_score'])
        
        CNB_result = prediction(X,Y,X_test,Y_test,distribution='CNB', created=created_time)
        modelResult.append(CNB_result)
        csvData += "{},{},{},{}".format(CNB_result['distribution'],CNB_result['accuracy'],CNB_result['recall_score'],CNB_result['precision_score'])

        BERN_result = prediction(X,Y,X_test,Y_test,distribution='BERN', created=created_time)
        modelResult.append(BERN_result)
        csvData += "{},{},{},{}".format(BERN_result['distribution'],BERN_result['accuracy'],BERN_result['recall_score'],BERN_result['precision_score'])
        
        removeAndWriteFile(dir_path+'7-prediction-result.json', modelResult)
        removeAndWriteFile(dir_path+'7-prediction-comparison.csv', csvData, 'csv')
        
        # To mongo
        print(i,"----->insert")
        insert_result = result_col.insert_many(modelResult)
        print(insert_result)