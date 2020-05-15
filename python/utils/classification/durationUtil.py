import re, math

class Duration:
    NOT_DEFINE = "Not Define" #type 0
    ONEDAY      = "1 Day" #type 1
    TWODAYS     = "2 Days" #type 2
    THREEDAYS   = "3 Days" #type 3
    FOURDAYS    = "4 Days" #type 4
    FIVEDAYS    = "5 Days" #type 5
    SIXDAYS     = "6 Days" #type 6
    SEVENDAYS   = "7 Days" #type 7
    EIGHTDAYS   = "8 Days" #type 8
    NINEDAYS    = "9 Days" #type 9
    TENDAYS     = "10 Days" #type 10
    ELEVENDAYS  = "11 Days" #type 11
    TWELVEDAYS  = "12 Days" #type 12
    MORE = "More than 12 Days" #type 13

numEng = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eigth', 'nine', 'ten', 'eleven', 'twelve', 'thirteen']
numTH = ['หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า', 'สิบ', 'สิบเอ็ด', 'สิบสอง', 'สิบสาม']

def chooseDuration(numDay):
    duration = { "type": None, "days": None, "label": Duration.NOT_DEFINE }
    d_type = math.ceil(numDay/3) if numDay >= 1 and numDay <= 12 else 5
    if (numDay == 1): duration = { "type": d_type, "days": numDay, "label": Duration.ONEDAY }
    elif (numDay > 1 and numDay <= 12): duration = { "type": d_type, "days": numDay, "label": "{} Days".format(numDay) }
    elif (numDay > 12): duration = { "type": d_type, "days": numDay, "label": Duration.MORE }
    return duration

"""
- วันที่สอง 2 ไม่ได้ตามด้วยเดือน
- แบบ 3 วัน 2 คืน หรือ 4 วัน 3 คืน (เลือกเอาอันที่มากที่สุด)
- คืน (ไม่มีคำว่า วัน)
- Day 1, day 2
TODO - เดินทางตั้งแต่ 28/3/2559 ถึง 1/4/2559
@params content all content from topic's owner including comments
"""
def findDuration(content,tags):
    # print("------------Duration")
    # keywords = [
    #     "ตลอดระยะเวลา",
    # ]
    # TODO

    if "One Day Trip" in tags:
        days = 1
        return math.ceil(days/3) , { "days": days, "label": Duration.ONEDAY }

    duration = None
    numAfter = 0
    numBefore = 0

    foundIndex = 0
    currentIndex = 0
    while (duration == None and foundIndex != -1 and currentIndex < len(content)):
        # print(foundIndex, currentIndex)
        # print(content[currentIndex:])
        searchResult = re.search(r'วัน|day|คืน',content[currentIndex:])
        if searchResult != None: foundIndex = searchResult.start()
        else: break
        # print("match idx",foundIndex, "-> ",content[foundIndex:foundIndex+10])
        i = currentIndex + foundIndex - 1
        # print(searchResult.start(), searchResult.group())

        # include one day pass
        num = 0
        while i >= foundIndex + currentIndex - 10 and i >= 0 :
            if num != 0: 
                numBefore = num if num > numBefore else numBefore
                break
            
            # print("s -> ",s)
            s = content[i: currentIndex + foundIndex].replace(" ","")
            if (i >= foundIndex - 4 and s.isdigit()): num = int(s)
            elif s in numTH: num = numTH.index(s) + 1
            elif s in numEng: num = numEng.index(s) + 1
            
            i -= 1

        if numBefore > 0 and (searchResult.group() == 'คืน' or searchResult.group() == 'วัน'): 
            numBefore = numBefore + 1 if searchResult.group() == 'คืน' else numBefore  #3คืน duration must be 4-6days
            duration = chooseDuration(numBefore)
            break

        isWanTee = searchResult.group() == 'วัน' and content[searchResult.end():searchResult.end()+3] == 'ที่' #เจอ วันที่
        isKeunTee = searchResult.group() == 'คืน' and content[searchResult.end():searchResult.end()+3] == 'ที่' #เจอ คืนที่
        if ((searchResult.group() == 'day') or  isWanTee or isKeunTee) and numBefore == 0: # check more of day 1, day 2, .... only 'day' word
            i = foundIndex + 3 if not isWanTee and not isKeunTee else foundIndex + 6
            s = content[i:i+10].replace(" ","") #check only 10 characters after 'day'
            n = re.findall(r'[0-9]+',s)
            if len(n) > 0: 
                maxx = int(max(re.findall(r'[0-9]+',s)))
                if isKeunTee:
                    maxx += 1
                if numAfter < maxx: numAfter = maxx
            # keep only max numAfter to declear duration

        currentIndex += foundIndex + 3
    #complete find วัน|day|คืน - check Do it has to use numAfter or not, numbefore has higher priority
    if (duration == None): #case: numBefore+Day and numAfter
        numMax = numBefore if numBefore > numAfter else numAfter
        duration = chooseDuration(numMax)

    return duration["type"], { "days": duration["days"], "label": duration["label"] }

