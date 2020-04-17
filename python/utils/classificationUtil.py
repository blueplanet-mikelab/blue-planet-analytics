import re, json, os
this_file_abs_path = os.path.abspath(os.path.dirname(__file__))
travel_guide_path = os.path.join(this_file_abs_path, 'travel_guide_average_071119.json' )
country_list_path = os.path.join(this_file_abs_path, 'countriesListSorted.json' )

# get country list to classify country and find top country
with open(travel_guide_path,'r', encoding="utf8") as travel_file:
    TRAVELGUIDELIST = json.load(travel_file) 

with open(country_list_path,'r', encoding="utf8") as json_file:
    COUNTRYLIST = json.load(json_file)  

# print('ประเทศเกาหลีเหนือ'.find("เกาหลีเหนือ")) 

"""
- ไทย: ในประเทศ, all thai provinces//done
- ญป: โอซาก้า เกียวโต คันไซ
- อเมริกา: นิวยอร์ก
เอาเมืองใส่ตอนหาในแท๊กด้วย แต่ก็ต้องระวัง push ประเทศซ้ำ
"""
def findCountries(tags, titleTokens, descTokens):    
    # print("----------Country")
    foundList = []
    for tag in tags:
        if (tag.find("เขต") == 0 or tag.find("เที่ยวในประเทศ") != -1 or tag == "การท่องเที่ยวแห่งประเทศไทย") and "TH" not in [c["country"] for c in foundList]:
            foundList.append([country for country in COUNTRYLIST if country["country"] == "TH"][0])
        
        startTag = ["คนไทยใน","เที่ยว","อาหาร","ประวัติศาสตร์"]
        for st in startTag:
            if tag.find(st) == 0:
                tag.replace(st,"")
        
        # print(tag, len(foundList))
        for country in COUNTRYLIST:
            for thaiName in country['nameThai']:
                # print(tag,thaiName, tag.find(thaiName))
                if tag.find(thaiName) != -1 and country["country"] not in [c["country"] for c in foundList]:
                    # print("tag:",tag)
                    if thaiName == 'เกาหลี' and tag.find("เกาหลีเหนือ") != -1: #exception
                        continue
                    else:
                        foundList.append(country)
                        break
    # print(len(foundList))
    # print(foundList)
    
    
    #1 if found list is not found -> search more in content using TITLE
    if len(foundList) == 0:
        for country in COUNTRYLIST:
            if country['nameEnglish'].lower() in titleTokens:
                foundList.append(country)
                continue

            for token in titleTokens:
                l = [thaiName for thaiName in country['nameThai'] if token == thaiName and thaiName != "จีน"] # some word consist of จีน but doesn't mean China
                if len(l) != 0 and country["country"] not in [c["country"] for c in foundList]:
                    foundList.append(country)
                    break #append once per country
    
    #2 if found list is not found -> search more in content using DESCRIPTION and COMMENTS
    if len(foundList) == 0:
        for country in COUNTRYLIST:
            if country['nameEnglish'].lower() in descTokens:
                foundList.append(country)
                continue

            for token in descTokens:
                l = [thaiName for thaiName in country['nameThai'] if token == thaiName and thaiName != "จีน"] # some word consist of จีน but doesn't mean China
                if len(l) != 0 and country["country"] not in [c["country"] for c in foundList]:
                    foundList.append(country)
                    break #append once per country
    
    # remove Thailand if it has tag "เที่ยวต่างประเทศ"
    if any("เที่ยวต่างประเทศ" in tag for tag in tags):
        foundList = [c for c in foundList if not (c["country"] == 'TH')]
    
    return foundList


"""
# หน้าหลังตัวย่อภาษาอังกฤษต้องไม่ใช่ตัวภาษาอังกฤษ
Finding a month that forum's owner travelled
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findMonth(content):
    # print("---------Month")
    wholeYearKeywords = [
        "365วัน","1ปี"
    ]
    monthKeywords = [
        ['มกรา', 'มค\\.', 'ม\\.ค', 'Jan', 'January',"ปีใหม่","นิวเยียร์"],
        ['กุมภา', 'กพ\\.', 'ก\\.พ', 'Feb', 'February',"เดือน2"],
        ['มีนา', 'มีค\\.', 'มี\\.ค', 'Mar', 'March',"เดือน3"],
        ['เมษา', 'เมย\\.', 'เม\\.ย', 'Apr', 'April',"เดือน4"],
        ['พฤษภา', 'พค\\.', 'พ\\.ค', 'May', 'May',"เดือน5"],
        ['มิถุนา', 'มิย\\.', 'มิ\\.ย', 'June', 'June',"เดือน6"],
        ['กรกฎา', 'กค\\.', 'ก\\.ค', 'July', 'July',"เดือน7"],
        ['สิงหา', 'สค\\.', 'ส\\.ค', 'Aug', 'August',"เดือน8"],
        ['กันยา', 'กย\\.', 'ก\\.ย', 'Sep', 'September',"เดือน9"],
        ['ตุลา', 'ตค\\.', 'ต\\.ค', 'Oct', 'October',"เดือน10"],
        ['พฤศจิกา', 'พย\\.', 'พ\\.ย', 'Nov', 'November',"เดือน11"],
        ['ธันวา', 'ธค\\.', 'ธ\\.ค', 'Dec', 'December',"เค้าท์ดาวน์","วันส่งท้ายปีเก่า","เดือน12"]
    ]

    monthCount = []

    #find whole year first
    rex = '|'.join(wholeYearKeywords)
    for match in re.compile(rex, re.IGNORECASE).finditer(content):
        return [month[4] for month in monthKeywords]

    #specific year
    for keyword in monthKeywords:
        rex = '|'.join(keyword) 
        rex = r'' + rex
        matchs = []
        for match in re.compile(rex, re.IGNORECASE).finditer(content):
            i = match.start()
            word = match.group()
            if word.lower() == keyword[3].lower() and (bool(re.search(r'[a-zA-Z]',content[i-1])) or bool(re.search(r'[a-zA-Z]',content[i+1]))):
                continue # skip Mar(ket)
            matchs.append(word)
        if len(matchs) != 0:
            monthCount.append(keyword[4])

    return monthCount if len(monthCount) != 0 else None


"""
# "budget": findBudget("คนละ 1000 คนละ 2,000 คนละ 3xxx คนละ 4+++ คนละ 5,xxx คนละ 6,+++ คนละ7พัน คนละพัน คนละเก้าพัน"),
TODO find budget using money words
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findBudgetByPattern(content):
    # print("---------Budget")
    digitAfterWords = [
        "ด้วยเงิน","ราคารวม","ทั้งหมดรวม","รวมค่าเสียหาย","จบแค่","คนละ","งบจำกัด","รวม"
    ]
    digitBeforeWords = [
        "บาทต่อท่าน","ต่อคน","ต่อท่าน","บาท","บ.","บาท/คน"
    ]
    moneyWords = [
        {"key":"แสน", "val":100000},
        {"key":"หมื่น","val":10000},
        {"key":"พัน","val":1000},
        {"key":"ร้อย","val":100},
        {"key":"สิบ","val":10} 
        # คนละพันบาท
    ]
    candidate = []
    
    # 1. digi after words
    rex = r'' + '|'.join(digitAfterWords)
    # print(rex)
    for m in re.compile(rex).finditer(content):
        i = m.start() + 3 #3 is the minimun length of keyword
        # print(m.start(),m.group())

        number = "0"

        # คนละพันบาท
        # rex = r'' + '|'.join([ key["key"] for key in moneyWords])
        # result = re.findall(rex, content[i:i+10])
        # print("result:", result)
        # if len(result) > 0:
        #     number = [d["val"] for d in moneyWords if d["key"] == result[0]][0]
        #     candidate.append(int(number))
        #     continue
        # คนละสี่พัน คนละ4พัน ยังไม่สำเร็จ

        sum = 0
        while(i < len(content) and i < m.start()+50):
            # print(i,content[i])
            if content[i].isdigit():
                # 41000
                # print("if1")
                number += content[i]
            elif number != "0" and content[i] == ',':
                # print("if2")
                # 41,xxx
                if content[i+1] == 'x' or content[i+1] == '+':
                    number += "000"
                    i += 3
                    while(content[i+1] == 'x' or content[i+1] == '+'): # 4,xxxx xเกิน
                        i += 1
                # 41,000 ผ่าน , ไปทำตัวถัดไป
            elif number != "0" and (content[i] == '+' or content[i] == 'x'):
                # print("if3")
                # รวม 857+957+23
                if (content[i] == '+' and content[i+1] != '+'):
                    sum += int(number)
                    number = "0"
                # ราคา 8+++ หรือ 4xxx
                else:
                    n = content[i]
                    # find length of xx..x or ++..+
                    while(content[i] == content[i+1]):
                        n += content[i+1]
                        i += 1
                    # define +++ or xxx as 000
                    for i in range(len(n)): 
                        number += "0"
            elif number != "0" and not content[i].isdigit():
                # print("if4")
                if sum != 0:
                    sum += int(number)
                    candidate.append(sum)
                else:
                    candidate.append(int(number))
                break # candidate: [4000, 13, 6000, 500, 1, 197, 30, 7, 9423]
            i += 1
    # print("candidate:",candidate)

    # 2. digit before word
    # may be nost necessary

    # next step find the maximun price as approximate budget แต่ถ้าน้อยกว่า 100 ไม่นับ
    budget = -1
    for c in candidate:
        if c > 100 and c > budget:
            budget = c
    return budget if budget != -1 else None

"""
@params 
    countries is list of sorted country
    days is numbers of travelling days
"""
def calculateBudget(countries, days):
    # print("--------calculateBudget--------")
    if len(countries) == 0 or days == None:
        return None
    
    cost = [travel_guide for travel_guide in TRAVELGUIDELIST if travel_guide["country_code"].lower()==countries[0]["country"].lower()]
    # print(cost)

    if len(cost) == 0:
        return None 
    else:
        # print("len(cost) != 0")
        totalCost = 0
        days = days/len(cost)
        for ccost in cost:
            flightOutbound = ccost["flight_price"]["outbound_6months_avg"]
            flightReturn = ccost["flight_price"]["return_6months_avg"]
            hotelPrice = ccost["hotel_price"]["year_avg"] * days
            inexpensiveMeal = 2 * ccost["daily_cost"]["inexpensive_meal"]
            midRangeMeal = ccost["daily_cost"]["mid_range_meal"]
            transportation = 4 * ccost["daily_cost"]["one_way_transportation"]
            daysCost = days * (inexpensiveMeal + midRangeMeal + transportation)
            
            totalCost += flightOutbound + flightReturn + hotelPrice + daysCost
        # print(totalCost)
        return totalCost


"""
find theme from keywords (first only using test searching) 
TODO add more keywords
TODO using tags
TODO next use image analytic
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findThemeByKeyWord(content,tags):
    themeKeywords = [
        ['Mountain', 'เขา', 'ภู', 'เดินป่า',"camping","แคมป์","น้ำตก", "ทะเลสาบ","ป่าไม้",'เล่นน้ำตก','ล่องแก่ง'], # start with ภู
        ['Sea', 'ทะเล', 'ดำน้ำ', 'ชายหาด', 'ปะการัง','โต้คลื่น'],
        ['Religion', 'ศาสนา', 'วัด',"สิ่งศักดิ์สิทธิ์","พระ","เณร","โบสถ์","มัสยิด"], # หน้าวัด ห้าม ห
        ['Historical', 'โบราณสถาน', 'ประวัติศาสตร์'], #ดูจาก tags
        ['Entertainment', 'สวนสนุก', 'สวนสัตว์','สวนน้ำ','สวนสยาม','คาสิโน','อควาเรียม'],
        ['Festival', 'งานวัด', 'งานกาชาด','เทศกาล','จัดแสดง'],
        ['Eatting', 'อาหาร', 'ร้านอาหาร', 'ขนม', 'ของหวาน',"ร้านกาแฟ", "อร่อย", 'ชา', 'เครื่องดื่ม','ของกิน','รสชาติ','คาเฟ่','ตลาดนัด'], # อาหาร แค่คำว่า match
        ['NightLifeStyle', 'ตลาดนัดกลางคืน',"ตลาดกลางคืน","ร้านกลางคืน","ร้านเหล้า","เหล้า","บาร์","เบียร์"],
        ['Photography', 'ภาพถ่าย', 'ถ่ายรูป','วิว','ถ่าย', 'ทริปถ่ายภาพ', 'ทริปถ่ายรูป', 'กล้อง','ตากล้อง'],
    ]

    text = content + ''.join(tags)
    themes = []
    for keyword in themeKeywords:
        rex = r'' + '|'.join(keyword)
        # print(rex)
        # รอบ regilion -> หน้าวัด ห้าม ห
        if "วัด" in keyword:
            match = []
            for m in re.compile(rex).finditer(text):
                if m.group == 'วัด':
                    if text[m.start()-1] != 'ห':
                        match.append(m.group())
                else:
                    match.append(m.group())
                # print(m.start(), m.group(), text[m.start()])
        # themes อื่นๆ
        else:
            match = re.findall(rex, text, re.IGNORECASE)
        # print(match)

        themes.append({ "theme": keyword[0], "count": len(match) })

    themes = sorted(themes, key = lambda i: (i['count'], i['theme']), reverse=True) 
    # pprint(monthCount)

    return [t for t in themes[:4] if t["count"] != 0]


