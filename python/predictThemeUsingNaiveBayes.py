import urllib.request, json, os, pymongo
from math import sqrt, exp, pi

from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import cleanContent, getStopWords

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

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
        print(class_label,"----init->",len(class_dict["topic_ids"]),"/",float(total_rows),"=",probabilities[class_label])
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
            
        print("----count:",count[class_label])
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

    #! 1. read models and listword
    with open('./5-themeModels-finish.json','r', encoding="utf8") as theme_json:
        themeModels = json.load(theme_json)
    with open('5-allwordList.json','r', encoding="utf8") as allword_json:
        allWordList = json.load(allword_json)

    #! 2-1. get data
    topicID = 39396463
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
    freqDict = {"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength}

    threadScores = calculateFullTFIDF([freqDict])
    threadScore = threadScores[0]

    #! 4. cut off some keys using tfidf by scores
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

    #! 4-1. Predict
    threadThemes = []
    for theme, model in themeModels.items(): #model = {"yes":..., "no":...}
        print("-----------",theme, "-----------")
        isTheme = predict(model, tscoresList, allWordList)
        print(theme,"is",isTheme)
        # break
        if isTheme == "yes":
            threadThemes.append(theme)

    print("-----------------------------------------------")
    print("Themes:",threadThemes)