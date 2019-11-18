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
from utils.measurementsUtil import accuracy, confusionMatrix, recallScore, precisionScore

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

# Calculate the Gaussian probability distribution function for x
def calculate_probability(x, mean, stdev):
	exponent = exp(-((x-mean)**2 / (2 * stdev**2 )))
	return (1 / (sqrt(2 * pi) * stdev)) * exponent

# Calculate the probabilities of predicting each class for a given row
def calculate_class_probabilities(model, toPredWord, allWordList):
    total_rows = sum([len(model[label]["topic_ids"]) for label in model])
    probabilities = {}
    count = {}
    for class_label, class_dict in model.items():
        # init
        count[class_label] = 0
        probabilities[class_label] = len(class_dict["topic_ids"])/float(total_rows)
        # print(class_label,"----init->",len(class_dict["topic_ids"]),"/",float(total_rows),"=",probabilities[class_label])
        if len(class_dict["topic_ids"]) == 1: #exclude
            probabilities[class_label] = -1
            break
        
        for word in allWordList:
            x = [w["count"] for w in toPredWord if w["key"]==word]
            toPredWordCount = x[0] if len(x) > 0 else 0
            y = [valDict for key, valDict in class_dict["words_count"].items() if key==word]
            if len(y) == 0:
                continue #not care other words outside class 
            mean = y[0]["mean"]
            stdev = y[0]["stdev"]
            # print("---word:{},x:{},m:{},std:{}".format(word,toPredWordCount,mean,stdev))
            probabilities[class_label] *= calculate_probability(toPredWordCount, mean, stdev)
            if probabilities[class_label] < (10**(-100)):
                probabilities[class_label] = probabilities[class_label] * (10**100)
                count[class_label] +=1
            elif probabilities[class_label] > (10**(100)):
                probabilities[class_label] = probabilities[class_label] * (10**(-100))
                count[class_label] -=1 
            # if first:
            #     print(">>",probabilities[class_label])
            
        # print("----count:",count[class_label])
    return probabilities, count

# Predict the class for a given row
def predict(model, toPredWord, allWordList):
    probabilities, countDict = calculate_class_probabilities(model, toPredWord, allWordList)
    if len(probabilities) != len(model):
        return "cannot predict model because of less data"
    print("prop:",probabilities)
    print("count:", countDict)
    bestCount = -999999
    for cclass, count in countDict.items():
        if count > bestCount:
            bestCount = count
            bestClass = cclass
        # print(cclass, count, "but best ->", bestClass, bestCount)
    if len([c for c in countDict.values() if c==bestCount]) > 1:
        bestKeys = [k for k, v in probabilities.items() if v == bestCount]
        bestProp, bestClass = -1, None
        for key in bestKeys:
            currentProp = probabilities[key]
            if bestClass == None:
                bestClass = key
                bestProp = currentProp
            elif currentProp > bestProp:
                bestProp = currentProp
                bestClass = key
    return bestClass

def training(trainDataset):
    print("----------Word Summary-----------")
    freqDictList = []
    for idx, thread in enumerate(trainDataset):
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
    removeAndWriteFile('1-wordsummary-train.json', freqDictList)

    #! 2. calculate IDF
    threadsScores = calculateFullTFIDF(freqDictList, '2-IDFScoreByWord-train.json') # consists of TF, IDF, and TFIDF scores
    #! 3. TFIDF calculation
    removeAndWriteFile('3-threadsScores-train.json', threadsScores)
    
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
    removeAndWriteFile('4-cutThreadsScores-train.json', threadsScores)

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

    removeAndWriteFile('5-allwordList-train.json', allWordList)
    
    #! 5.1 Find mean and stdev of each word in each class
    print("------> calculate mean stdev")
    for idx, theme in enumerate(themeModels):
        for classTheme in themeModels[theme]:
            # print(theme,"----", classTheme)
            length = len(themeModels[theme][classTheme]["topic_ids"])
            for word, numbers in themeModels[theme][classTheme]["words_count"].items():
                mean = calMean(numbers, length)
                themeModels[theme][classTheme]["words_count"][word] = {
                    "mean": mean,
                    "stdev": calStdev(numbers, mean, length),
                    "length":length
                }

    removeAndWriteFile('5-themeModels-train.json', themeModels)
    return themeModels, allWordList


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

    threadsCount = len(threadsList)
    split = int(threadsCount * 0.8)
    trainDataset = threadsList[:split]
    testDataset = threadsList[split:]
    print("trainDataset:", len(trainDataset), "| testDataset:", len(testDataset))

    #! 0. create Model
    themeModels, allWordList = training(trainDataset)

    #! 1. read models and listword
    # with open('./5-themeModels-train.json','r', encoding="utf8") as theme_json:
    #     themeModels = json.load(theme_json)
    # with open('5-allwordList-train.json','r', encoding="utf8") as allword_json:
    #     allWordList = json.load(allword_json)

    #! 2-1. get data
    print("----TEST------Word Summary-----------")
    freqDictList = []
    for idx, thread in enumerate(testDataset):
        topicID = thread['TopicID']
        print(idx,"--",topicID)

        with urllib.request.urlopen(URLCONFIG["mike_thread"] + str(topicID)) as url:
            threadData = json.loads(url.read().decode())
    
        #! 2-2. retrieve title+destription+comment
        title = threadData['_source']['title']
        desc = threadData['_source']['desc']
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID]
        rawContent = title + desc + ' '.join(comments)

        #! 2-3. tokenize+wordsummary
        wordsSum, tokensLength, wordSumDict = createWordsSummary(cleanContent(rawContent), getStopWords(addMore=True))
        # freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength, "created_at":datetime.datetime.now()})
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength})

    threadScores = calculateFullTFIDF(freqDictList)

    #! 3 prediction and prepare data to measure
    values = {
        'Mountain':       {"actual":[], "predict":[], 'topicOrder':[]},
        'Entertainment':  {"actual":[], "predict":[], 'topicOrder':[]},
        'Photography':    {"actual":[], "predict":[], 'topicOrder':[]},
        'Eating':         {"actual":[], "predict":[], 'topicOrder':[]},
        'WaterActivities':{"actual":[], "predict":[], 'topicOrder':[]},
        'Religion':       {"actual":[], "predict":[], 'topicOrder':[]},
        'Honeymoon':      {"actual":[], "predict":[], 'topicOrder':[]},
        'Backpack':       {"actual":[], "predict":[], 'topicOrder':[]},
        'Event':          {"actual":[], "predict":[], 'topicOrder':[]}
    }
    for threadScore in threadScores:
        currentTopicID = threadScore["topic_id"]
        print("------",currentTopicID, "-----------")
        #! 3-1. cut off some keys using tfidf by scores
        tscoresList = threadScore['scores']
        if len(tscoresList) > 100:
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

        threadScore['significant_words'] = tscoresList
        # tscoresList = [{
        #     "key": "ที่อื่น",
        #     "count": 1,
        #     "tf": 0.0014144271570014145,
        #     "idf": 1.8082887711792655,
        #     "tfidf": 0.00255769274565667
        # },...]

        actualThemes = [thread["Theme"] for thread in testDataset if thread["TopicID"] == currentTopicID][0]
        #! 3-2. prediction
        predictedThemes = []
        for theme, model in themeModels.items(): #model = {"yes":..., "no":...}
            # print("-----------",theme, "-----------")
            isTheme = predict(model, tscoresList, allWordList)
            print(theme,"is",isTheme)
            # break

            actualVal = 1 if theme in actualThemes else 0
            predictVal = 1 if isTheme == "yes" else 0
            values[theme]["actual"].append(actualVal)
            values[theme]["predict"].append(predictVal)
            values[theme]['topicOrder'].append(currentTopicID)

            if isTheme == "yes":
                predictedThemes.append(theme)

        print("-----------------------------------------------")
        threadScore['actual_themes'] = actualThemes
        threadScore['predicted_themes'] = predictedThemes
        print(currentTopicID, "Themes:",predictedThemes)
    
    removeAndWriteFile('6-values-test.json', values)
    removeAndWriteFile('6-threadScores-test.json', themeModels)

    #! 4 measurements
    for theme, valDict in values.items():
        actualVal = valDict["actual"]
        predictVal = valDict["predict"]
        values[theme]["accuracy"] = accuracy(actualVal, valDict)
        values[theme]["confusion_matrix"] = confusionMatrix(actualVal, valDict)
        values[theme]["recall_score"] = recallScore(actualVal, valDict)
        values[theme]["precision_score"] = precisionScore(actualVal, valDict)
    removeAndWriteFile('7-measurements-test.json', values)