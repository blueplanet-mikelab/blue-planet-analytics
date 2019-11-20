import pymongo, json, urllib.request, time
from urllib.error import URLError, HTTPError
import os,sys
import re
path_to_current = "D:/AOM_Document/blue-planet-pantip-analytics/python/"
sys.path.append(path_to_current)
os.chdir(path_to_current)

from utils.fileWritingUtil import removeAndWriteFile, readTXTFile, readJSONFile

with open('./config/url.json') as json_data_file:
    URLCONFIG = json.load(json_data_file)
TARGETROOM = "บลูแพลนเน็ต"

def listAllPantipThread():
    path_to_pantipTrend = "../pantip_trend/"
    fileList = os.listdir(path_to_pantipTrend)
    print(len(fileList))
    currentDate = ""
    blueplanetThreadList = {}
    for idx, fileName in enumerate(fileList):
        print(idx+1, fileName)
        currentDate = re.findall(r'(\d+)_',fileName)[0]
        # print(currentDate)
        if currentDate not in blueplanetThreadList:
            blueplanetThreadList[currentDate] = []

        path_to_file = path_to_pantipTrend + fileName 
        topicIDList = readTXTFile(path_to_file).split("\n")

        # print(topicIDList)
        
        for topicID in topicIDList:
            if len(topicID) <= 1:
                continue
            # print(URLCONFIG["mike_thread"]+topicID)
            try:
                with urllib.request.urlopen(URLCONFIG["mike_thread"]+topicID) as url:
                    threadData = json.loads(url.read().decode())
                    if TARGETROOM in threadData["_source"]["rooms"] and topicID not in blueplanetThreadList[currentDate]:
                        blueplanetThreadList[currentDate].append(topicID)
            except HTTPError as e:
                print(topicID,'-> Error code: ', e.code)
            except URLError as e:
                print(topicID,'-> Reason: ', e.reason)

        time.sleep(3)
        # if idx==5:
        #     break
    print(blueplanetThreadList)
    removeAndWriteFile('./pantipThreadList.json', blueplanetThreadList)

def fixDuplicateDate():
    topicList = readJSONFile('./pantipThreadList.json')
    allTopic = []
    for date, topics in topicList.items():
        nonDuplicate = []
        for topic in topics:
            if topic not in allTopic:
                allTopic.append(topic)
                nonDuplicate.append(topic)
        topicList[date] = nonDuplicate
    return topicList


if __name__ == "__main__":
    # listAllPantipThread()
    newTopicList = fixDuplicateDate()
    removeAndWriteFile('./pantipThreadList-new.json', newTopicList)
