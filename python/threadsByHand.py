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

from utils.TFIDFCalculationUtil import calculateFullTFIDF
from utils.fileWritingUtil import removeAndWriteFile


# prepare stopwords list
def getStopWords(fname, addMore=True):
    stopwords = pycorpus.common.thai_stopwords()
    stopwordsList = set(m.strip() for m in stopwords)
    if addMore:
        f = open(fname, "r", encoding='utf-8') #"./stopwords_more_th.txt"
        stopwordsList = stopwordsList.union(set(m.strip() for m in f.readlines()))
    return stopwordsList

def createWordsSummary(content, stopwordsList):
    # tokenize
    tokens = word_tokenize(content, engine='attacut-sc')
    # print(tokens)
    
    # stopword remove
    stopwordsList.update(["\xa0", " "])
    # new_tokens = [token for token in tokens if token not in stopwordsList]
    new_tokens = []
    for token in tokens:
        if token not in stopwordsList and len(token) > 1:
            new_tokens.append(token)
        elif token == "น.":
            new_tokens.pop() # take the time out

    # word summarization (word count)
    wordsSum = {}
    for token in new_tokens:
        wordsSum[token] = 1 if token not in wordsSum else wordsSum[token] + 1
    
    wordsSumArray = []
    for k,v in wordsSum.items():
        wordsSumArray.append({'word': k, 'count': v})

    return wordsSumArray, len(new_tokens)

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
        
        with urllib.request.urlopen("http://ptdev03.mikelab.net/kratooc/"+topicID) as url:
            threadData = json.loads(url.read().decode())
            # print(threadData)

        #! 1. retrieve title+destription+comment
        title = threadData['_source']['title']
        desc = threadData['_source']['desc']
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID]
        rawContent = title + desc + ' '.join(comments)

        #! 2. tokenize+wordsummary
        rawContent = re.sub(r'<[^<]+/>|<[^<]+>|\\.{1}|&[^&]+;|\n|\r\n','', rawContent) # to msg_clean
        wordsSum, tokensLength = createWordsSummary(cleanContent(rawContent), getStopWords("./stopwords_more_th.txt"))
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
    


