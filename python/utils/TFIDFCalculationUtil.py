import os
import json
import math

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

def createWordsSummary(tokens, stopwordsList):
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

    return wordsSumArray, len(new_tokens), wordsSum

# tf = (frequency of the term in the doc/total number of terms in the doc)
# idf = ln(total number of dics/number of docs with term in it)
def calculateFullTFIDF(freqDictList, fname=None):
    print("---------calculateFullTFIDF--------")
    idfDict = {} # keep idf score which have already computed
    if fname!=None and os.path.isfile(fname):
        with open('./'+fname,'r', encoding="utf8") as json_file:
            idfDict = json.load(json_file)

    Scores_docs = []
    for idx, freqDict in enumerate(freqDictList):
        tid = freqDict["topic_id"]
        print(idx, "----", tid)
        scores = []
        for keys in freqDict["words_sum"]:
            currentWord = keys['word']
            tf =  keys['count']/ freqDict["tokens_length"]
            
            if currentWord in idfDict.keys():
                idf = idfDict[currentWord]
            else:
                count = 0
                for tempDict in freqDictList:
                    for k in tempDict["words_sum"]:
                        if k['word'] == currentWord:
                            count += 1
                idf = math.log(len(freqDictList)/count)
                idfDict[currentWord] = idf

            tfidf = tf*idf

            scores.append({
                'key': currentWord,
                'count': keys['count'],
                'tf': tf,
                'idf': idf,
                'tfidf': tfidf
            })

        sorted_scores = sorted(scores,key=lambda x:x['tfidf'],reverse=True)
        Scores_docs.append({
            'topic_id': tid,
            'scores': sorted_scores,
            # 'token_length': freqDict["tokens_length"]
        })

    # write output txt file
    if fname != None:
        with open('./'+fname, 'w', encoding="utf8") as outfile:
            json.dump(idfDict, outfile, ensure_ascii=False, indent=4)
    
    return Scores_docs

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
    
    return DF_scores_docs