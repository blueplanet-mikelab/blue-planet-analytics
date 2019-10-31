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

# tf = (frequency of the term in the doc/total number of terms in the doc)
def computeTF( freqDictList):
    TF_scores_docs = []
    for idx, freqDict in enumerate(freqDictList):
        tid = freqDict["topic_id"]
        print(idx, "----", tid)
        TF_scores = {}
        for keydict in freqDict["words_sum"]:
            key = keydict['word']
            TF_scores[key] =  keydict['count']/ freqDict["tokens_length"]
        
        TF_scores_docs.append({
            'topic_id': tid,
            'tf_scores': TF_scores
        })
    return TF_scores_docs

# idf = ln(total number of dics/number of docs with term in it)
def computeIDF(freqDictList, fname='IDFScoreByWord.json'):
    helperDict = {} # keep idf score which have already computed
    if os.path.isfile(fname):
        with open('./'+fname,'r', encoding="utf8") as json_file:
            helperDict = json.load(json_file)

    IDF_scores_docs = []
    for idx, freqDict in enumerate(freqDictList):
        print(idx, "----", freqDict['topic_id'])
        IDF_scores = {}
        for keys in freqDict["words_sum"]:
            currentWord = keys['word']
            if currentWord in helperDict.keys():
                score = helperDict[currentWord]
            else:
                count = 0
                for tempDict in freqDictList:
                    for k in tempDict["words_sum"]:
                        if k['word'] == currentWord:
                            count += 1
                score = math.log(len(freqDictList)/count)
                helperDict[currentWord] = score
            IDF_scores[currentWord] = score

        IDF_scores_docs.append({
            'topic_id': freqDict["topic_id"],
            'idf_scores': IDF_scores
        })

    # write output txt file
    with open('./'+fname, 'w', encoding="utf8") as outfile:
        json.dump(helperDict, outfile, ensure_ascii=False, indent=4)
    
    return IDF_scores_docs

def computeTFIDF(TF_scores, IDF_scores):
    TFIDF_scores_docs = []
    # each topic
    for idx, idf_topic in enumerate(IDF_scores):
        for tf_topic in TF_scores:
            if idf_topic['topic_id'] == tf_topic['topic_id']:
                print(idx, "----", idf_topic['topic_id'])
                TFIDF_scores = {}
                # each key in topics
                for tfkey, tfscore in tf_topic['tf_scores'].items():
                    for idfkey, idfscore in idf_topic['idf_scores'].items():
                        if tfkey == idfkey:
                            TFIDF_scores[tfkey] = idfscore * tfscore
                sortedDict = { k : v for k, v in sorted(TFIDF_scores.items(), key=lambda x: x[1], reverse=True)}
                TFIDF_scores_docs.append({'topic_id':idf_topic['topic_id'], 'tfidf_scores':sortedDict})
                break # if topic match continute to next topic

    return TFIDF_scores_docs

def computeDF(tfidfList, fname):
    DF_scores_docs = {}
    for idx, tfidfTopic in enumerate(tfidfList):
        print(idx, "---", tfidfTopic['topic_id '])
        for scores in tfidfTopic["tfidf_scores"]:
            currentWord = scores['key']
            if currentWord not in DF_scores_docs.keys():
                count = 0 # number of docs that havs the key
                for tempTopic in tfidfList:
                    for k in tempTopic["tfidf_scores"]:
                        if k['key'] == currentWord:
                            count += 1
                            break
                dfScore = count/len(tfidfList)
                DF_scores_docs[currentWord] = dfScore

    # write output txt file
    with open('./'+fname, 'w', encoding="utf8") as outfile:
        json.dump(DF_scores_docs, outfile, ensure_ascii=False, indent=4)
    
    return DF_scores_docs

def removeAndWriteFile(fname, content, ftype='json'):
   if os.path.isfile(fname):
      os.remove(fname)
      print("remove",fname,"success")

   if ftype == 'txt':
      f = open(fname, "w",encoding='utf-8')
      f.write(content)
      print("create",fname,"success")
      f.close() 
   elif ftype == 'json':
      with open('./'+fname, 'w', encoding="utf8") as outfile:
         json.dump(content, outfile, ensure_ascii=False, indent=4)
         print("create",fname,"success")
   else:
      print("invalid file type")

if __name__ == "__main__":
    # client = pymongo.MongoClient("hostname",
    #                             27017,
    #                             username='username',
    #                             password='password',
    #                             authSource='admin' )
    # db = client["dbname"] #TODO database access

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
        # print("title:",title)
        desc = threadData['_source']['desc']
        # print("desc:",desc)
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID]
        # print("comments:")
        # print(' '.join(comments))
        rawContent = title + desc + ' '.join(comments)

        #! 2. tokenize+wordsummary
        rawContent = re.sub(r'<[^<]+/>|<[^<]+>|\\.{1}|&[^&]+;|\n|\r\n','', rawContent) # to msg_clean
        # removeAndWriteFile('test.txt',cleanContent(rawContent),'txt')
        wordsSum, tokensLength = createWordsSummary(cleanContent(rawContent), getStopWords("./stopwords_more_th.txt"))
        # freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength, "created_at":datetime.datetime.now()})
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength})


    #! 3. push to mongo   
    # wordsum_col = db["word_summary"]
    # result = wordsum_col.insert_many(freqDictList)
    # print("result--",result)
    removeAndWriteFile('1-wordsummary.json', freqDictList)

    #! 4. TFIDF calculation
    # tfidf_col = db["scores_tfidf"]
    print("----------TF-----------")
    tfScores = computeTF(freqDictList)
    print("----------IDF-----------")
    idfScores = computeIDF(freqDictList)
    print("----------TF_IDF-----------")
    tfidfScores = computeTFIDF(tfScores,idfScores)
    removeAndWriteFile('2-tfidfScores.json', tfidfScores)
    
    # for tfidfThread in tfidfScores:
    #     tfidfDict = tfidfThread['tfidf_scores']
    #     if len(tfidfDict) > 100:
    #         for key, score in list(tfidfDict.items()):
    #             # print(key, ":", score)
    #             if score < 0.0035 or score > 0.02:
    #                 # print("del:", key)
    #                 del tfidfDict[key]
    #         tfidfThread['tfidf_scores'] = { k : v for k, v in sorted(tfidfDict.items(), key=lambda x: x[1], reverse=True)}
    # removeAndWriteFile('2-tfidfScores-valcut.json', tfidfScores)

    for tfidfThread in tfidfScores:
        tfidfDict = tfidfThread['tfidf_scores']
        if len(tfidfDict) > 100:
            sortedDict = { k : v for k, v in sorted(tfidfDict.items(), key=lambda x: x[1], reverse=True)}
            # headcut = int(0.1*len(sortedDict))
            headcut = 0
            tailcut = len(sortedDict) - int(0.46*len(sortedDict))
            prevVal = -1
            for idx, key in enumerate(list(sortedDict)):
                if prevVal == -1:
                    prevVal = sortedDict[key]

                if (idx < headcut or idx > tailcut) and sortedDict[key] != prevVal:
                    del sortedDict[key]
                else:
                    prevVal = sortedDict[key]

            tfidfThread['tfidf_scores'] = sortedDict
    removeAndWriteFile('2-tfidfScores-percent.json', tfidfScores)

    # result = tfidf_col.insert_many(tfidfScores)
    # print("result--",result)

    # #! 5. Vector calculation
    # print("----------vector creation-----------")
    # dfScoresfname = "keysDFScores.json"
    # if os.path.isfile(dfScoresfname):
    #     with open('./'+dfScoresfname,'r', encoding="utf8") as json_file:
    #         dfScoresDict = json.load(json_file)
    # else:
    #     dfScoresDict = computeDF(tfidfScores, fname=dfScoresfname)
    
    # #! 5.2 Words selection
    # themesVector = []
    # # at least 1 theme and no more than 4 per thread -> only count more than 5 per theme
    # for i, thread in enumerate(threadsList):
    #     topicID = thread["TopicID"]
    #     tokens = [[key['key'] for key in tfidf["tfidf_scores"]] for tfidf in tfidfScores if tfidf["topic_id"]==topicID][0]
        
    #     minn = 0.0006
    #     wordsBag = [[key['key'] for key in tfidf["tfidf_scores"] if key['score'] > minn] for tfidf in tfidfScores if tfidf["topic_id"]==topicID][0]
    #     print(i,"--",topicID,"--", len(tokens), "->", len(wordsBag),"--m:", minn)
    #     # print(wordsBag)
        
    #     threadsThemeList = thread["Theme"].replace(" ","").split(",") #string
    #     for idx, theme in enumerate(threadsThemeList):
    #         if not [vec for vec in themesVector if vec['type']==theme]: #create new theme
    #             themesVector.append({'type':theme, 'topic_ids':[topicID], 'word_vectors':{}})
            
    #         for vector in themesVector: # select which theme to add
    #         # print("vector theme:",vector['type'])
    #             if vector['type'] == theme:
    #                 vector["topic_ids"].append(topicID)
                
    #                 for word in wordsBag:
    #                     # print("word:",word)
    #                     if word not in vector['word_vectors'].keys():
    #                         # print("word not found in key")
    #                         vector['word_vectors'][word] = dfScoresDict[word] if word in dfScoresDict.keys() else 0
    #                     # if word has already in 'word_vectors', it don't need to do anything.
    #                 break # there is only one theme vector per theme
    #     # break # 1 thread
    
    # removeAndWriteFile('3-themesVector'+minn+'.json',themesVector,'json')

    # #! 5.3 Sorted
    # for vector in themesVector:
    #     print("----theme:", vector['type'])
    #     print("before sorted:", len(vector["word_vectors"]))
    #     vector["word_vectors"] = [{'word':k,'val': v} for k, v in sorted(vector["word_vectors"].items(), key=lambda x: x[1], reverse=True)]
    #     print("after sorted:", len(vector["word_vectors"]))
    #     # vector["created_at"] = datetime.datetime.now()
   
    # fname = '4-sortedThemesVector.json'
    # removeAndWriteFile(fname,themesVector,'json')

    # vector_col = db["vector_theme"]
    # vector_col.drop()
    # result = vector_col.insert_many(themesVector)
    # print(result)


