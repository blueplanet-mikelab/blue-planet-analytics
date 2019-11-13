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
from math import sqrt, exp, pi
from utils.TFIDFCalculationUtil import calculateFullTFIDF, createWordsSummary
from utils.fileWritingUtil import removeAndWriteFile


# prepare stopwords list
def getStopWords(fname, addMore=True):
    stopwords = pycorpus.common.thai_stopwords()
    stopwordsList = set(m.strip() for m in stopwords)
    if addMore:
        f = open(fname, "r", encoding='utf-8') #"./stopwords_more_th.txt"
        stopwordsList = stopwordsList.union(set(m.strip() for m in f.readlines()))
    return stopwordsList

def cleanContent(rawContent):
    # clean text
    content = rawContent
    url_rex = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    content = re.sub(url_rex,'', content) #1 remove url
    content = re.sub(r'â|ä|à|å|á|ã', 'a', content) #2 replace extended vowels a
    content = re.sub(r'Ä|Å|Á|Â|À|Ã', 'A', content) #3 replace extended vowels A
    content = re.sub(r'ê|ë|è', 'e', content) #4 replace extended vowels e
    content = re.sub(r'É|Ð|Ê|Ë|È', 'E', content) #5 replace extended vowels E
    content = re.sub(r'ï|î|ì|í|ı', 'i', content) #6 replace extended vowels i
    content = re.sub(r'Í|Î|Ï', 'I', content) #7 replace extended vowels I
    content = re.sub(r'ô|ö|ò|ó|õ', 'o', content) #8 replace extended vowels o
    content = re.sub(r'Ö|Ó|Ô|Ò|Õ', 'O', content) #9 replace extended vowels O
    content = re.sub(r'ü|û|ù|ú', 'u', content) #10 replace extended vowels u
    content = re.sub(r'Ü|Ú|Û|Ù', 'U', content) #11 replace extended vowels U
    content = re.sub(r'ç', 'c', content) #12 replace extended chars c
    content = re.sub(r'ÿ|ý', 'y', content) #13 replace extended chars y
    content = re.sub(r'Ý', 'Y', content) #14 replace extended chars y
    content = re.sub(r'ñ|Ñ', 'n', content) #15 replace extended chars n
    content = re.sub(r'ß', 's', content) #16 replace extended chars n
    # spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    spechar = r'[^a-zA-Zก-๙\s]+|\xa0+|ๆ' #! take numbers out
    content = re.sub(spechar, ' ', content) #17 remove special character
    #18 remove duplicate characters and spaces
    dupGroup = re.finditer(r'\s{2,}|([ก-๙a-zA-Z])\1{2,}', content)
    dupArray = [[c.start(), c.end()] for c in dupGroup]
    # print(dupArray)
    newContent = ""
    if len(dupArray) == 0:
        newContent = content
    else:
        prevIdx = 0
        for idxDup in dupArray:
            newContent += content[prevIdx:idxDup[0]+1]
            prevIdx = idxDup[1]
        newContent += content[prevIdx:]
    return newContent

    # Calculate the mean of a list of numbers
def mean(numbers, length):
	return sum(numbers)/length
 
# Calculate the standard deviation of a list of numbers
def stdev(numbers, avg, length):
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
        
        with urllib.request.urlopen("http://ptdev03.mikelab.net/kratooc/"+topicID) as url:
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
        wordsSum, tokensLength, wordSumDict = createWordsSummary(tokens, getStopWords("./stopwords_more_th.txt"))
        # freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength, "created_at":datetime.datetime.now()})
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
    allThemeList = ['Mountain', 'Entertainment', 'Photography', 'Eating', 'WaterActivities', 'Religion', 'Honeymoon', 'Backpack', 'Event']
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
                if key not in themeModels[theme][isTheme]['words_count'].keys():
                    themeModels[theme][isTheme]['words_count'][key] = []
                themeModels[theme][isTheme]['words_count'][key].append(word['count'])
    
    removeAndWriteFile('5-themeModels-notyet.json', themeModels)
            
                    

