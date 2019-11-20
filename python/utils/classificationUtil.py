import re, json

# get country list to classify country and find top country
with open('./travel_guide_average_071119.json','r', encoding="utf8") as travel_file:
    TRAVELGUIDELIST = json.load(travel_file) 

"""
- ไทย: ในประเทศ, all thai provinces//done
- ญป: โอซาก้า เกียวโต คันไซ
- อเมริกา: นิวยอร์ก
เอาเมืองใส่ตอนหาในแท๊กด้วย แต่ก็ต้องระวัง push ประเทศซ้ำ
@params tags array of tags
        countryList from json file
"""
def findCountries(tags, countryList, content):    
    # print("----------Country")
    foundList = []
    for tag in tags:
        for country in countryList:
            # skip if that country has already in the list
            if True in [country['country'] in found['country'] for found in foundList]:
                continue

            for thaiName in country['nameThai']:
                # print(tag,thaiName)
                if tag.find(thaiName) != -1 and country["country"] not in [c["country"] for c in foundList]:
                    # print("tag:",tag)
                    foundList.append(country)

    # if found list is not found -> search more in content
    if len(foundList) == 0:
        for country in countryList:
            for thaiName in country['nameThai']:
                if content.find(thaiName) != -1 and country["country"] not in [c["country"] for c in foundList]:
                    # print("content:",country["nameEnglish"])
                    foundList.append(country)
    
    if any("เที่ยวต่างประเทศ" in tag for tag in tags):
        foundList = [c for c in foundList if not (c["country"] == 'TH')]

    return foundList


"""
# หน้าหลังตัวย่อภาษาอังกฤษต้องไม่ใช่ตัวภาษาอังกฤษ
Finding a month that forum's owner travelled
#TODO whole year in Backend
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findMonth(content):
    # print("---------Month")
    # wholeYearKeywords = [
    #     "365วัน","1ปี"
    # ]
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
    for keyword in monthKeywords:
        rex = '|'.join(keyword)
        rex = r'' + rex
        matchs = []
        for match in re.compile(rex, re.IGNORECASE).finditer(content):
            i = match.start()
            word = match.group()
            if word.lower() == keyword[3].lower() and (bool(re.search(r'[a-zA-Z]',content[i-1])) or bool(re.search(r'[a-zA-Z]',content[i+1]))):
                continue
            matchs.append(word)

        monthCount.append({ "month": keyword[4], "count": len(matchs) })
    monthCount = sorted(monthCount, key = lambda i: (i['count'], i['month']), reverse=True) 
    return monthCount

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
    return budget


"""
find theme from keywords (first only using test searching) 
TODO add more keywords
TODO using tags
TODO next use image analytic
@params msg_clean the first topic's owner message
        comments list of all comments by topic's owner
"""
def findThemeByKeyword(content,tags):
    themeKeywords = [
        ['Entertainment', 'สวนสนุก', 'สวนสัตว์'],
        ['Water Activities', 'ทะเล', 'สวนน้ำ', 'สวนสยาม', 'ดำน้ำ', 'เล่นน้ำตก', 'ว่ายน้ำ', 'ล่องแก่ง'],
        ['Religion', 'ศาสนา', 'วัด',"สิ่งศักดิ์สิทธิ์","พระ","เณร"], # หน้าวัด ห้าม ห
        ['Mountain', 'เขา', 'ภู', 'เดินป่า',"camping","แคมป์","น้ำตก"], # start with ภู
        ['Backpack', 'แบกเป้', ' แบกกระเป๋า'], #ดูจาก tags
        ['Honeymoon', 'ฮันนีมูน',"โรแมนติก","คู่รัก","สวีท","เดท"],
        ['Photography', 'ภาพถ่าย', 'ถ่ายรูป','วิว','ถ่าย'],
        ['Eatting', 'อาหาร', 'ร้านอาหาร', 'ขนม', 'ของหวาน',"ร้านกาแฟ", "อร่อย", 'ชา', 'เครื่องดื่ม','ของกิน','รสชาติ', 'คาเฟ่'], # อาหาร แค่คำว่า match
        ['Event', 'งานวัด', 'งานกาชาด', 'เทศกาล', 'เฟสติวัล']
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

    return themes


"""
@params 
    countries is list of sorted country
    days is numbers of travelling days
"""
def calculateBudget(countries, days):
    cost = [travel_guide for travel_guide in TRAVELGUIDELIST["country_code"]==countries[0]["country"]]
    if len(cost) == 0:
        return -1  
    else:
        flightOutbound = cost["flight_price"]["outbound_6months_avg"]
        flightReturn = cost["flight_price"]["return_6months_avg"]
        hotelPrice = cost["hotel_price"]["year_avg"] * days
        inexpensiveMeal = 2 * cost["daily_cost"]["inexpensive_meal"]
        midRangeMeal = cost["daily_cost"]["mid_range_meal"]
        transportation = 4 * cost["daily_cost"]["one_way_transportation"]
        daysCost = days * (inexpensiveMeal + midRangeMeal + transportation)
        return flightOutbound + flightReturn + hotelPrice + daysCost