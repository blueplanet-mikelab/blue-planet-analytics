import re, pprint
import urllib.request, json 

from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import cleanContent, getStopWords, tokenization, createWordsSummary

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)

def grouping(tokens, length):
    tokenLength = len(tokens)
    wordGroupList = []
    groupCount = tokenLength - 1
    print(tokenLength, groupCount)

    for i in range(tokenLength - length + 1) :
        words = []
        for j in range(length):
            w = tokens[i+j]
            words.append((w, wordSumDict[w]))
        wordGroup = ''.join([word[0] for word in words])

        if wordGroup not in [wg["group"] for wg in wordGroupList]:
            wordGroupList.append({
                "group": wordGroup,
                "count": 1,
                "words":words
            })
        else:
            cdict = [wg for wg in wordGroupList if wg["group"] == wordGroup][0]
            cdict["count"] += 1
    
    
    return wordGroupList

# pprint.pprint([wordGroup for wordGroup in wordGroupList if wordGroup["wordGroupCount"] > 1])
def multipleGrouping(tokens,length):
    print("length:",length)
    if length == 1:
        return []
    
    wordGroupList = grouping(tokens,length)
    if len(wordGroupList) == 0:
        return []

    considered = []
    for wordGroup in wordGroupList:
        if wordGroup["count"] > 1:  
            wordGroup["totalDiff"] = sum([w[1]-wordGroup["count"] for w in wordGroup['words']])/ wordGroup["count"]
            considered.append(wordGroup)

    # considered = sorted(considered,key=lambda x:x['count'],reverse=True)
    # considered = sorted(considered,key=lambda x:x['count'])
    # pprint.pprint(considered)

    stopWords = getStopWords(addMore=True)
    cutNum = 0.4
    removed = [conWord for conWord in considered if len(set([w[0] for w in conWord["words"]]) - set(stopWords)) == len(conWord["words"]) and conWord["totalDiff"] <= cutNum]
    # pprint.pprint(removed)
    print(len(considered), len(removed))

    #remove token
    selected = [w[0] for remo in removed for w in remo["words"] ]
    new_tokens = [token for token in tokens if token not in selected]
    print(selected)
    return removed + multipleGrouping(new_tokens,length-1)


if __name__ == "__main__":

    print("----------Word Summary-----------")
    topicID = 39330414

    with urllib.request.urlopen(URLCONFIG["mike_thread"]+str(topicID)) as url:
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
    tokens = tokenization(cleanContent(rawContent), getStopWords(addMore=True), removeStopWord=False)
    wordsSum, tokensLength, wordSumDict = createWordsSummary(tokens)
    # pprint.pprint(wordSumDict)
    # freqDict = {"topic_id": topicID, "words_sum": wordsSum, "tokens_length": tokensLength}

    #! 1-3. oc-curance
    startLength = 3
    groupList = multipleGrouping(tokens,startLength)
    groups = [group["group"] for group in groupList]
    pprint.pprint(groupList)
    print(groups)
