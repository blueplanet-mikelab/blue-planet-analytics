// fetch 

const fs = require('fs');
const moment = require('moment')
// const db = require('monk')('localhost/pantip-blueplanet')
const db = require('monk')(process.env.MONGODB_URI, { authSource: 'admin' })

const axios = require('axios')
// TODO from Mongo instead
const countriesList = JSON.parse(fs.readFileSync("./json/countries-list-th-eng.json")) //Object
const countriesListTH = Object.keys(countriesList)
const NOT_DEFINE = "Not Define" //type 0

const durationEnum = {
    ONETHREE: "1 to 3 Days", //type 1
    FOURSIX: "4 to 6 Days", //type 2
    SEVENNINE: "7 to 9 Days", //type 3
    TENTWELVE: "10 to 12 Days", //type 4
    MORE: "More", //type 5
}

function findThumbnail(descFull) {
    // <img class="img-in-post" src="https://f.ptcdn.info/642/063/000/pqgvvokmjZYsnUCJtk3-o.jpg" data-image
    if (descFull == undefined) return NOT_DEFINE

    const startText = '<img class="img-in-post" src="'
    const endText = '" data-image'
    let i = descFull.search(startText)
    let j = descFull.search(endText)
    if (i != -1 && j != -1) {
        return descFull.substring(i + startText.length, j)
    }

    return NOT_DEFINE
}

function findCountryFromTags(tags) {
    for (tag of tags) {
        for (country of countriesListTH) {
            if (tag.includes(country)) {
                return countriesList[country]
            }
        }
    }
    return NOT_DEFINE
}

function findDuration(str) {
    // searchTexts = ['วัน', 'day']
    let numEng = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eigth', 'nine', 'ten', 'eleven', 'twelve', 'thirteen']
    let numTH = ['หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า', 'สิบ', 'สิบเอ็ด', 'สิบสอง', 'สิบสาม']
    let duration = { type: 0, label: NOT_DEFINE }

    let foundIndex = 0
    let currentIndex = 0
    while (duration.label == NOT_DEFINE && foundIndex != -1 && currentIndex < str.length) {

        foundIndex = str.substring(currentIndex).search(/วัน|day/i)
        // console.log('foundIndex:', foundIndex)
        // console.log('substr:',str.substring(currentIndex))
        // console.log('text',str.charAt(foundIndex+currentIndex),str.charAt(foundIndex+currentIndex+1))
        let i = currentIndex + foundIndex - 1
        // console.log('consider text:',str.substring(foundIndex+currentIndex-10,foundIndex+currentIndex-1))
        // console.log("i", i)
        // console.log("si"+str.charAt(i)+'<<')
        let j = 0
        while (i >= foundIndex - 10 && i >= 0) {
            const s = str.substring(i, currentIndex + foundIndex).replace(/\s/g, '')
            // console.log("in while2")
            // console.log("s"+ s+"<<")
            if ((i >= foundIndex - 4 && !isNaN(parseInt(s)))) {
                // console.log("j in number", j)
                j = parseInt(s)
                // console.log('j=',j)
                break
            } else if (numTH.includes(s) || numEng.includes(s)) {
                // console.log("j in numtext", j)
                j = numTH.indexOf(s) + 1
                // console.log('j=',j)
                break;
            }

            i--;
        }
        // console.log("j", j)

        // if (j < 0) duration = {type: 0, label: NOT_DEFINE}
        if (j > 0 && j <= 3) duration = { type: 1, label: durationEnum.ONETHREE }
        else if (j > 3 && j <= 6) duration = { type: 2, label: durationEnum.FOURSIX }
        else if (j > 6 && j <= 9) duration = { type: 3, label: durationEnum.SEVENNINE }
        else if (j > 9 && j <= 12) duration = { type: 4, label: durationEnum.TENTWELVE }
        else if (j > 12) duration = { type: 5, label: durationEnum.MORE }

        if (duration.label != NOT_DEFINE) {
            // console.log('d:',duration)
            break
        }

        currentIndex += foundIndex + 3
        // console.log("ci", currentIndex)
        // console.log('d:',duration, '|-f:', foundIndex, '|-ci:', currentIndex, '|-strl:', str.length)
    }
    return duration

}

function findSeason(str) {
    const months = [
        ['มกรา', 'มค\\.', 'ม\\.ค', 'Jan', 'January'],
        ['กุมภา', 'กพ\\.', 'ก\\.พ', 'Feb', 'February'],
        ['มีนา', 'มีค\\.', 'มี\\.ค', 'Mar', 'March'],
        ['เมษา', 'เมย\\.', 'เม\\.ย', 'Apr', 'April'],
        ['พฤษภา', 'พค\\.', 'พ\\.ค', 'May', 'May'],
        ['มิถุนา', 'มิย\\.', 'มิ\\.ย', 'June', 'June'],
        ['กรกฎา', 'กค\\.', 'ก\\.ค', 'July', 'July'],
        ['สิงหา', 'สค\\.', 'ส\\.ค', 'Aug', 'August'],
        ['กันยา', 'กย\\.', 'ก\\.ย', 'Sep', 'September'],
        ['ตุลา', 'ตค\\.', 'ต\\.ค', 'Oct', 'October'],
        ['พฤศจิกา', 'พย\\.', 'พ\\.ย', 'Nov', 'November'],
        ['ธันวา', 'ธค\\.', 'ธ\\.ค', 'Dec', 'December']
    ]

    let monthCount = []
    for (let month of months) {
        let re = new RegExp(month.reduce((prev, cur) => prev + '|' + cur), 'gi')
        const matchArray = str.match(re) || []
        // console.log('matchArray: ', matchArray)
        monthCount.push({ month: month[4], count: matchArray.length })
    }
    monthCount.sort((a, b) => b.count - a.count)

    // console.log(monthCount)
    return monthCount
}

// findTheme from tags
function findTheme(tags) {
    const themes = [
        ['Adventure', 'สวนสนุก'],
        ['Water Activities', 'ทะเล', 'สวนน้ำ', 'สวนสยาม', 'ดำน้ำ', 'น้ำตก', 'ว่ายน้ำ', 'ล่องแก่ง'],
        ['Religion', 'ศาสนา', 'วัด','ไหว้พระ','บุญ'], // หน้าวัด ห้าม ห
        ['Mountain', 'เขา', 'ภู', 'เดินป่า'] // start with ภู
        ['Backpack'],
        ['Honeymoon', 'ฮันนีมูน'],
        ['Photography', 'ภาพถ่าย', 'ถ่ายรูป'],
        ['Eating', 'อาหาร', 'ร้านอาหาร', 'ขนม', 'ของหวาน'] // อาหาร แค่คำว่า match
    ]
    console.log(themes)
}

const fetchDetail = async () => {
    console.log('start fetch detail')
    const topicIDList = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json'))
    console.log(topicIDList.length)

    const created = moment().format()

    // TODO from mongo
    // const topicIDList = db.get('topReadTopics').find()

    let smartData = []
    for (i = 0; i < topicIDList.length; i++) {
        const element = topicIDList[i]
        let smartObject = {}
        const topicID = element.topicID
        console.log(i, ' TopicID: ', topicID)
        try {
            const response = await axios.get('http://ptdev03.mikelab.net/kratooc/' + topicID)
            const detail = response.data._source

            smartObject.topicID = topicID
            smartObject.title = detail.title
            smartObject.desc = detail.desc
            smartObject.thumbnail = findThumbnail(detail.desc_full) // TODO if desc_full not have find in comment of poster
            smartObject.country = findCountryFromTags(detail.tags) // TODO find country in desc
            smartObject.duration = findDuration(detail.title + ' ' + detail.desc) // TODO include comment by poster
            smartObject.season = findSeason(detail.title + ' ' + detail.desc) // TODO include comment by poster
            smartObject.theme = NOT_DEFINE // TODO
            smartObject.budget = NOT_DEFINE // TODO
            smartObject.view = element.view
            smartObject.score = {
                view: element.view,
                emotionSum: detail.emotion.sum,
                commentLength: detail.comment_count,
                point: detail.point,
                topicType: detail.type
            }
            smartObject.link = detail.permalink

            smartObject.created = created
            smartData.push(smartObject)

            // Add to DB
            if ((i % 1000 == 0 || i == topicIDList.length - 1) && i != 0) {
                try {
                    const result = await db.get('smartDataTest').insert(smartData)
                    console.log('inserted 1000 topics, i:', i);
                    smartData.length = 0 // clear array
                } catch (err) {
                    console.log('error to insert', err)
                }
            }

        } catch (err) {
            // no internet
            if (err.code == 'ENOTFOUND')
                console.log('not internet connection')
            // topic not found
            else if (err.response.status == 404)
                console.log('cannot fetch ', topicID, 'topic may be deleted')
            // retry
            else
                i = i - i % 1000
        }
        // console.log(smartObject)
        // break;
    };

    return smartData

}

const fetchTest = async () => {
    let topicID = '38454943'
    let detail = {}
    try {
        const response = await axios.get('http://ptdev03.mikelab.net/kratooc/' + topicID)
        detail = response.data._source


    } catch (err) {
        console.log('test -> cannot fetch ', topicID)
        console.log(err)
    }
}

// fetchTest()

// Push all at once
// fetchDetail().then(smartData => {
//     console.log(typeof smartData)
//     console.log(smartData.length)
//     db.get('smartData1').insert(smartData)
//         .then(result => { console.log('inserted smartData'); db.close() })
//         .catch(err => console.log('error to insert', err))
// })

// Push every 1000 documents
fetchDetail()
    .then(() => db.close())
