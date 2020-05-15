import os, sys
import re
from datetime import datetime
sys.path.insert(0, "./utils")

from classification.classificationUtil import findMonth, findCountries, calculateBudget, findThemeByKeyWord, findBudgetByPattern, calculatePopularity, findThumbnail
from manageContentUtil import firstClean, cleanContent, fullTokenizationToWordSummary
from classification.durationUtil import findDuration

"""
Create a preprocessing document for each topic
@params totalView a number of view of the forum
        totalVote a number of votes for the forum
        totalComment a number of comment on the forum
        createdDate date of create the forum
"""
def createPreprocessData(threadData):
    title = threadData['title']
    desc = threadData['desc']
    userID = threadData['uid']
    comments = [comment['desc'] for comment in threadData['comments'] if comment['uid']==userID]
    rawContent = title + desc + ' '.join(comments)
    
    tags = threadData["tags"]
    titleTokens, _ = fullTokenizationToWordSummary(cleanContent(title), maxGroupLength=3)
    descTokens, _ = fullTokenizationToWordSummary(cleanContent(desc + ' '.join(comments)), maxGroupLength=3)
    countries = findCountries(tags, titleTokens, descTokens) # array of string
    if len(countries) == 0:
        return None

    content = firstClean(rawContent)
    spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    content = re.sub(spechar, ' ', content) #17 remove special character
    
    month = findMonth(content) # array of month with count
    
    d_type, duration = findDuration(content,threadData["tags"])
    days = duration["days"]
    budget = findBudgetByPattern(content) #None or number
    # print("budget:", budget)
    if budget == None:
        budget = calculateBudget(countries, days) #None or number
    
    totalView = threadData['view']
    totalPoint = threadData["point"]
    totalComment = threadData["comment_count"]

    return {
        "topic_id": threadData["tid"],
        "title": title,
        "short_desc": desc[:250],
        "thumbnail": findThumbnail(threadData['tid']), 
        "countries": countries,
        "duration_type" : d_type,
        "duration" : duration,
        "month": month,
        "theme": findThemeByKeyWord(content,tags), #TODO using Naive Bayes
        "budget": budget,
        "view": totalView,
        "vote": totalPoint,
        "comment": totalComment,
        "viewvotecom_per_day": calculatePopularity(totalView,totalPoint,totalComment,int(threadData["created_time"])),
        "created_at": threadData["created_time"],
        "doc_created_at": datetime.now()
    }
