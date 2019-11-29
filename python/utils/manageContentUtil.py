import re
import pythainlp.corpus as pycorpus
from pythainlp.tokenize import word_tokenize,  dict_trie

def firstClean(rawContent):
    content = rawContent
    content = re.sub(r'<[^<]+/>|<[^<]+>|\\.{1}|&[^&]+;|\n|\r\n','', content) #0 to msg_clean
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
    return content

# prepare for tokenize
def cleanContent(rawContent):
    content = firstClean(rawContent)
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

def fullTokenizationToWordSummary(content,maxGroupLength, addCustomDict=True):
    custom_file, custom_trie = getCustomDictList(addCustomDict)
    
    firstTokens = word_tokenize(cleanContent(content), engine='attacut-sc', custom_dict=custom_trie)
    firstTokens = [token.lower() for token in firstTokens if token != ' ' and len(token) > 1]
    
    _, _, wordSumDict = createWordsSummary(firstTokens)
   
    groupList = multipleGrouping(firstTokens, maxGroupLength, wordSumDict)
    
    #update new group words to file
    groups = [group["group"] for group in groupList]
    with open('./utils/customdict_more_th.txt', 'a', encoding='utf-8') as filehandle:
        for group in groups:
            if group not in custom_file:
                filehandle.write('%s\n' % group)

    stopWordList = getStopWords(addMore=True)
    newTokens = combineTokenAndClean(firstTokens, groupList, stopWordList)
    newWordSumDict = addGroupsToWordSum(wordSumDict, groupList, stopWordList)

    return newTokens, newWordSumDict


# prepare stopwords list
def getStopWords(addMore, fname="./utils/stopwords_more_th.txt"):
    stopwords = pycorpus.common.thai_stopwords()
    stopwordsList = set(m.strip() for m in stopwords)
    f = open(fname, "r", encoding='utf-8')
    stopwordsList = stopwordsList.union(set(m.strip() for m in f.readlines()))
    return stopwordsList

# prepare stopwords list
def getCustomDictList(addMore, fname="./utils/customdict_more_th.txt"):
    wordsDict = set(pycorpus.common.thai_words())
    if addMore:
        f = open(fname, "r", encoding='utf-8')
        custom = []
        for m in f.readlines():
            wordsDict.add(str(m.strip()))
            custom.append(str(m.strip()))
    return custom, dict_trie(dict_source=wordsDict)

# def removeStopWords(tokens, stopwordsList):
#     new_tokens = []
#     for token in tokens:
#         if token not in stopwordsList and len(token) > 1:
#             new_tokens.append(token.lower())
#         elif token == "น.":
#             new_tokens.pop() # take the time out
#     return new_tokens


def createWordsSummary(tokens):
    # word summarization (word count)
    wordsSum = {}
    for token in tokens:
        wordsSum[token] = 1 if token not in wordsSum else wordsSum[token] + 1
    
    wordsSumArray = []
    for k,v in wordsSum.items():
        wordsSumArray.append({'word': k, 'count': v})

    return wordsSumArray, len(tokens), wordsSum


def grouping(tokens, length, wordSumDict):
    tokenLength = len(tokens)
    wordGroupList = []

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


def multipleGrouping(tokens,length, wordSumDict):
    if length == 1:
        return []
    
    wordGroupList = grouping(tokens,length, wordSumDict)
    if len(wordGroupList) == 0:
        return []

    considered = []
    for wordGroup in wordGroupList:
        if wordGroup["count"] > 1:  
            wordGroup["totalDiff"] = sum([w[1]-wordGroup["count"] for w in wordGroup['words']])/ wordGroup["count"]
            considered.append(wordGroup)

    # considered = sorted(considered,key=lambda x:x['count'],reverse=True)
    # pprint.pprint(considered)

    stopWords = getStopWords(addMore=True)
    cutNum = 0.4
    removed = [conWord for conWord in considered if len(set([w[0] for w in conWord["words"]]) - set(stopWords)) == len(conWord["words"]) and conWord["totalDiff"] <= cutNum]
    # pprint.pprint(removed)

    #remove token for next round
    selected = [w[0] for remo in removed for w in remo["words"] ]
    new_tokens = [token for token in tokens if token not in selected]
    return removed + multipleGrouping(new_tokens,length-1, wordSumDict)


def addGroupsToWordSum(oldWordSumDict, groupList, stopWordList):
    newWordSumDict = oldWordSumDict.copy()
    
    # add group and remove single 
    for group in groupList:
        newWordSumDict[group["group"]] = group["count"]
        selected = [word[0] for word in group["words"]]
        for key in selected:
            if key in newWordSumDict:
                subCount = newWordSumDict[key] - group["count"]
                if subCount == 0:
                    del newWordSumDict[key]
                else:
                    newWordSumDict[key] = subCount
    # remove stopwords
    for key in list(newWordSumDict.keys()):
        if key in stopWordList:
            del newWordSumDict[key]

    return newWordSumDict

def combineTokenAndClean(tokens, groupList, stopwordsList):
    selected = {}
    for group in groupList:
        selected[group["group"]] = [w[0] for w in group["words"]] 
    oldLength = len(tokens)
    for idx in range(oldLength):
        if idx == len(tokens): break

        # find if token in group
        for key, val in selected.items():
            if tokens[idx: idx+len(val)] == val:
                # print(len(val), tokens[idx: idx+len(val)])
                tokens[idx: idx+len(val)] = [key]
                break
        # check if current token is stopword or not
        if tokens[idx] in stopwordsList or len(tokens[idx]) <= 1:
            del tokens[idx]
            idx -= 1
    return tokens

