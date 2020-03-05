import csv, json
import re
import ssl, urllib.request
import sys
sys.path.insert(0, "./utils")
from fileWritingUtil import removeAndWriteFile
from manageContentUtil import fullTokenizationToWordSummary
from TFIDFCalculationUtil import calculateFullTFIDF

# with writing 1-4 file
def dataPreparationToThreadsScores(dir_path, URL):
    #! 0. read csv -> threadsList
    print('----------Import data from mike-----------')
    with open('./labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
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

    return threadsScores, threadTheme

if __name__ == "__main__":
    dataPreparationToThreadsScores('uiltest/', 'http://ptdev03.mikelab.net/kratooc/')