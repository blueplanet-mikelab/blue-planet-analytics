import csv, pprint, json
import ssl, urllib.request
import os, datetime, re, copy
import math, random
import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB
import pymongo
import numpy as np
from math import sqrt, exp, pi
from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import fullTokenizationToWordSummary
from utils.measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore


with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

dir_path = './naiveBayes-maxminscale/'

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
    return {
        'I1': score >= 0 and score < 1/3,
        'I2': score >= 1/3 and score < 2/3,
        'I3': score >= 2/3 and score <= 1
    }

def initializeWordCount(threadsScores):
    wordCount = {}
    for thread in threadsScores:
        for word in thread['significant_words']:
            if word['key'] not in wordCount.keys():
                wordCount[word['key']] = []
    return wordCount


def dataPreparationToCreateModel():
    #! 0. read csv -> threadsList
    with open('./labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
        # pprint.pprint(threadTheme)
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
        
        # if idx==2:
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
    emptyWordCount = initializeWordCount(threadsScores)
    for theme in allThemeList:
        copyOfEmptyWordCount = copy.deepcopy(emptyWordCount)
        themeModels[theme] = { 'topic_ids':[], 'words_count':copyOfEmptyWordCount }
    # pprint.pprint(themeModels)
    
    for i, thread in enumerate(threadsScores):
        topicID = thread["topic_id"]
        currentThreadTheme = threadTheme[topicID] #['Mountain','Sea']
        print(i,"--",topicID, currentThreadTheme)

        for idx, theme in enumerate(allThemeList):
            # print("current Theme:", theme)
            memberTheme = allThemeList[theme]
            #add topic id
            if any([mt in currentThreadTheme for mt in memberTheme]):
                # print("append:",theme)
                themeModels[theme]['topic_ids'].append(topicID)
            else:
                # print("skip")
                continue

            topicLength = len(themeModels[theme]['topic_ids'])
            
            #add word_count and word_list
            for word in thread['significant_words']:
                key = word['key']
                themeModels[theme]['words_count'][key].append(word['count']) #have to done everytime
                
            #!! word_list has -> thread word not have
            for key in themeModels[theme]['words_count']:
                countLength = len(themeModels[theme]['words_count'][key])
                # print(key,theme,'topic:',topicLength, 'count:',countLength, themeModels[theme]['words_count'][key])
                themeModels[theme]['words_count'][key].extend(np.zeros(topicLength-countLength).tolist())

    removeAndWriteFile(dir_path+'5-themeModels-onlycount.json', themeModels)
    
    #! 5 Naive Bayes model - apply MaxMinScale
    print("----------Naive Bayes model - apply MaxMinScale----------")
    for idx, theme in enumerate(themeModels):
        themeModels[theme]['words_maxminscale'] = {}
    #     themeModels[theme]['words_interval'] = {}
        if len(themeModels[theme]['topic_ids']) == 0:
            continue

        for word, count in themeModels[theme]['words_count'].items():
            scaler = MinMaxScaler()
            count_ndarray = np.array(count).reshape(-1, 1)
            scaler.fit(count_ndarray)
            maxmin_score = scaler.transform(count_ndarray).reshape(1, -1).tolist()[0]
            themeModels[theme]['words_maxminscale'][word] = maxmin_score
    #         themeModels[theme]['words_interval'][word] = [selectInterval(sc) for sc in maxmin_score]
    # pprint.pprint(themeModels)
    removeAndWriteFile(dir_path+'5-themeModels-maxmin-interval.json', themeModels)
    
    # insert model to mongo !FIXME error because exceed limit size of 16MB
    # model_col = db["naive_bayes_maxminscale"]
    # modelToInsert = [ 
    #     {'_id':key, 
    #     'topic_ids':themeDetail['topic_ids'], 
    #     'words_count':themeDetail['words_maxminscale']} 
    #     for key, themeDetail in themeModels.items()]
    # result = model_col.insert_many(modelToInsert)

def formatData():
    with open(dir_path+'5-themeModels-maxmin-interval.json') as json_data_file:
        print('read data')
        themeModels = json.load(json_data_file) 
        # {"Mountain": {
        #     'topic_ids':[...],
        #     'words_count':{'key':[...],...},
        #     'words_maxminscale':{'key':[...],...}
        #   },...
        # }
        print('finish reading data')

    # create model
    X = []
    Y = []
    for theme, themeDetail in themeModels.items():
        for idx, tid in enumerate(themeDetail['topic_ids']):
            Y.append(theme)
            mX = [scoreList[idx] for key, scoreList in themeDetail['words_maxminscale'].items()]
            X.append(mX)
    removeAndWriteFile(dir_path+'6-X-data-formatting.json', X)
    removeAndWriteFile(dir_path+'6-Y-data-formatting.json', Y)

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
    else:
        print("please input distribution code")
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
    # dataPreparationToCreateModel()
    # formatData()

    print('importing X and Y')
    with open(dir_path+'6-X-data-formatting.json') as json_data_file:
        X = json.load(json_data_file) 
        print('finish import X')

    with open(dir_path+'6-Y-data-formatting.json') as json_data_file:
        Y = json.load(json_data_file) 
        print('finish import Y')

    csvData = "Distribution, Accuracy, Recall, Precision\n"
    ranint = random.sample(range(303), 30)
    X_test = [X[i] for i in ranint]
    Y_test = [Y[j] for j in ranint]
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
        
        # removeAndWriteFile(dir_path+'7-prediction-result.json', modelResult)
        # removeAndWriteFile(dir_path+'7-prediction-comparison.csv', csvData, 'csv')
        
        # To mongo
        print(i,"----->insert")
        insert_result = result_col.insert_many(modelResult)
        print(insert_result)