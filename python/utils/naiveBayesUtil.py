import csv, json
import re
import ssl, urllib.request, os
import sys
sys.path.insert(0, "./utils")
from fileWritingUtil import removeAndWriteFile
from manageContentUtil import fullTokenizationToWordSummary
from TFIDFCalculationUtil import calculateFullTFIDF
this_file_abs_path = os.path.abspath(os.path.dirname(__file__))
labeled_threads_path = os.path.join(this_file_abs_path, '../labeledThreadsbyHand_v2.csv' )

# with writing 1-4 file
def dataPreparationToThreadsScores(dir_path, URL):
    #! 0. read csv -> threadsList
    print('----------Import data from mike-----------')
    with open(labeled_threads_path, 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
        # pprint.pprint(threadTheme)
        removeAndWriteFile(dir_path+'0-300threads.json', threadsList)
        removeAndWriteFile(dir_path+'0-threadsTheme.json', threadTheme)


    print("----------Word Summary-----------")
    freqDictList = []
    threadsCount = len(threadsList)
    for idx, thread in enumerate(threadsList):
        topicID = thread['TopicID']
        print(idx,"--",topicID)
        
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(URL+topicID, context=context) as url:
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

    #! 1-3. save to json  
    removeAndWriteFile(dir_path+'1-wordsummary.json', freqDictList)

    #! 2,3. calculate IDF and TFIDF calculation
    threadsScores = calculateFullTFIDF(freqDictList, dir_path+'2-IDFScoreByWord.json') # consists of TF, IDF, and TFIDF scores
    removeAndWriteFile(dir_path+'3-threadsScores.json', threadsScores)
    
    # scores to cut
    # if score < 0.0035 or score > 0.02:
    #     del tfidfDict[key]

    #! 4. cut off some keys using tfidf by scores
    newThreadsScores = []
    for thread in threadsScores:
        print(thread["topic_id"])
        tscoresList = []
        totalKeys = len(thread['scores'])
        if totalKeys > 100: #cut words if that threads has more than 100 words
            # headcut = int(0.1*totalKeys)
            headcut = 0
            tailcut = totalKeys - int(0.46*totalKeys) # cut at index..
            prevVal = -1
            # print(totalKeys, headcut, tailcut, totalKeys-tailcut)
            for idx, scores in enumerate(thread['scores']):
                if prevVal == -1:
                    prevVal = scores['tfidf']

                if (idx < headcut or idx > tailcut) and scores['tfidf'] != prevVal:
                    continue #remove!
                    # print("remove", idx)
                else:
                    # print(idx)
                    tscoresList.append(scores)
                    prevVal = scores['tfidf']
        newThreadsScores.append({
            "topic_id": thread["topic_id"],
            "significant_words": tscoresList
        })

    removeAndWriteFile(dir_path+'4-cutThreadsScores.json', newThreadsScores)

    return newThreadsScores, threadTheme

# use by naiveBayes-mmscale-interval-090320 -for-> test
#!NOTE  params: threadsScores is changed during the function
def cutoffKeys(dir_path, threadsScores):
    #! 4. cut off some keys using tfidf by scores
    newThreadsScores = []
    for thread in threadsScores:
        # print(thread["topic_id"])
        tscoresList = []
        totalKeys = len(thread['scores'])
        if totalKeys > 100: #cut words if that threads has more than 100 words
            # headcut = int(0.1*totalKeys)
            headcut = 0
            tailcut = totalKeys - int(0.46*totalKeys) # cut at index..
            prevVal = -1
            # print(totalKeys, headcut, tailcut, totalKeys-tailcut)
            for idx, scores in enumerate(thread['scores']):
                if prevVal == -1:
                    prevVal = scores['tfidf']

                if (idx < headcut or idx > tailcut) and scores['tfidf'] != prevVal:
                    continue #remove!
                    # print("remove", idx)
                else:
                    # print(idx)
                    tscoresList.append(scores)
                    prevVal = scores['tfidf']
        newThreadsScores.append({
            "topic_id": thread["topic_id"],
            "significant_words": tscoresList
        })

    removeAndWriteFile(dir_path+'4-cutThreadsScores.json', newThreadsScores)
    return newThreadsScores

def computeJaccardSimilarityScore(x, y):
    """
    Jaccard Similarity J (A,B) = | Intersection (A,B) | /
                                    | Union (A,B) |
    """
    intersection_cardinality = len(set(x).intersection(set(y)))
    union_cardinality = len(set(x).union(set(y)))
    return intersection_cardinality / float(union_cardinality)


# if __name__ == "__main__":
#     dataPreparationToThreadsScores('uiltest/', 'http://ptdev03.mikelab.net/kratooc/')