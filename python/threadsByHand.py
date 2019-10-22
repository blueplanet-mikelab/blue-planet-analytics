import csv
import pprint
import urllib.request, json 
from pythainlp.tokenize import word_tokenize
import pythainlp.corpus as pycorpus
import re
import math
import pymongo
import os


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
    # spechar = r'(\s+)|"|:|!|ๆ|~|#|@|\*|(\?)|\(|\)|\[|\]|\-|\+|•|\_|\/|>|<|^|(?<!\d)\.(?!\d)|(5{5,})|\=|\”|\“|♡|(?<!\d)\,(?!\d)|&|¥|฿|✿|([^a-zA-Z0-9ก-๙\s]+)'
    spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    content = re.sub(spechar, ' ', content) #17 remove special character
    #18 remove duplicate characters and spaces
    dupGroup = re.finditer(r'\s{2,}|([ก-๙Xx])\1{2,}', content)
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
        TF_scores = []
        for keydict in freqDict["words_sum"]:
            key = keydict['word']
            TF_scores.append({
                'score': keydict['count']/ freqDict["tokens_length"],
                'key' : key
            })
        TF_scores_docs.append({
            'topic_id': tid,
            'tf_scores': TF_scores
        })
    return TF_scores_docs

# idf = ln(total number of dics/number of docs with term in it)
def computeIDF(freqDictList, fname='IDFScoreByWord.json'):
    helperDict = {} # keep idf score which have already computed
    IDF_scores_docs = []
    for idx, freqDict in enumerate(freqDictList):
        print(idx, "----", freqDict['topic_id'])
        IDF_scores = []
        for keys in freqDict["words_sum"]:
            currentWord = keys['word']
            if currentWord in helperDict.keys():
                score = helperDict[currentWord]
            else:
                count = 0
                for tempDict in freqDictList:
                    for k in tempDict["words_sum"]:
                        if k['word'] == currentWord:
                            count += k['count']
                score = math.log(len(freqDictList)/count)
                helperDict[currentWord] = score
            IDF_scores.append({
                'score': score,
                'key' : currentWord
            })
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
                TFIDF_scores = []
                # each key in topics
                for tf in tf_topic['tf_scores']:
                    for idf in idf_topic['idf_scores']:
                        key = idf['key']
                        if tf['key'] == key:
                            TFIDF_scores.append({
                                'score': idf['score'] * tf['score'],
                                'key': key
                            })
                TFIDF_scores_docs.append({'topic_id':idf_topic['topic_id'], 'tfidf_scores':TFIDF_scores})
                break # if topic match continute to next topic

    return TFIDF_scores_docs

def computeDF(tfidfList, fname='keysDFScores.json'):
   DF_scores_docs = {}
   for idx, tfidfTopic in enumerate(tfidfList):
      print(idx, "---", tfidfTopic['_id'])
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

if __name__ == "__main__":
    client = pymongo.MongoClient("hostname",
                                27017,
                                username='username',
                                password='password',
                                authSource='admin' )
    db = client["dbname"] #TODO database access

    # read csv
    with open('./labeledThreadsbyHand.csv', 'r', encoding="utf8") as f:
        threads = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

    freqDictList = []
    # pprint.pprint(threads)
    # pprint.pprint(threads[0])
    threadsCount = len(threads)
    for idx, thread in enumerate(threads):
        topicID = thread['TopicID']

        with urllib.request.urlopen("http://ptdev03.mikelab.net/kratooc/"+topicID) as url:
            threadData = json.loads(url.read().decode())
            # print(threadData)

        #TODO 1. retrieve title+destription+comment
        title = threadData['_source']['title']
        # print("title:",title)
        desc = threadData['_source']['desc']
        # print("desc:",desc)
        userID = threadData['_source']['uid']
        comments = [comment['desc'] for comment in threadData['_source']['comments'] if comment['uid']==userID] # TODO comments not clean
        # print("comments:")
        # print('\n'.join(comments))
        rawContent = title + desc + ' '.join(comments)

        #TODO 2. tokenize+wordsummary
        wordsSum, tokensLength = createWordsSummary(cleanContent(rawContent), getStopWords("./stopwords_more_th.txt"))

        #TODO 3. push to mongo
        wordsum_col = db["word_summary"]
        freqDictList.append({"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength})
        result = wordsum_col.insert_many(freqDictList)
        print("result--",result)

        break
    
    #TODO 4. TFIDF calculation
    tfidf_col = db["scores_tfidf"]
    tfScores = computeTF(freqDictList)
    idfScores = computeIDF(freqDictList)
    tfidfScores = computeTFIDF(tfScores,idfScores)
    result = tfidf_col.insert_many(tfidfScores)
    print("result--",result)

    #TODO 5. Vector calculation
    dfScoresfname = "keysDFScores.json"
    if os.path.isfile(dfScoresfname):
      with open('./'+dfScoresfname,'r', encoding="utf8") as json_file:
         dfScoresDict = json.load(json_file)
    else:
        dfScoresDict = computeDF(tfidfScores, fname=dfScoresfname)
    
    #TODO 5.2