import re, pprint
import urllib.request, json 

from utils.fileWritingUtil import removeAndWriteFile
from utils.manageContentUtil import fullTokenizationToWordSummary

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)


if __name__ == "__main__":

    topicID = 39330414
    print("----------",topicID)

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
    tokens, wordSumDict = fullTokenizationToWordSummary(rawContent, maxGroupLength=3)
    print(tokens)
    print("------------")
    print(wordSumDict)

    print(len(tokens), len(wordSumDict))


    #! 1-3. oc-curance
    # startLength = 3
    # groupList = multipleGrouping(tokens,startLength, wordSumDict)
    # groups = [group["group"] for group in groupList]
    # pprint.pprint(groupList)
    # newWordSumDict = addGroupsToWordSum(wordSumDict, groupList)
    # print(groups)

    #! try to add wordDict
    # print(">>-------------------")
    # tokens2 = tokenization(cContent, removeStopWord=False, customDictList=groups)
    # pprint.pprint(tokens2)
    # _, _, wordSumDict2 = createWordsSummary(tokens2)
    # pprint.pprint(wordSumDict2)