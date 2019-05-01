// fetch 

const fs = require('fs');
var path = require('path');
const moment = require('moment')
// const db = require('monk')('localhost/pantip-blueplanet')
const axios = require('axios')
const countriesList = JSON.parse(fs.readFileSync("./json/countries-list-th-eng.json")) //Object
const countriesListTH = Object.keys(countriesList)

const durationEnum = {
    ONETHREE: "1 to 3 Days",
    FOURSIX: "4 to 6 Days",
    SEVENNINE: "7 to 9 Days",
    TENTWELVE: "10 to 12 Days",
    MORE: "More",
}

let smartData = []

function createReport(data, filename, dir) {
    data = data.sort(function (obj1, obj2) { return obj2.view - obj1.view })
    fs.writeFileSync(dir + filename, JSON.stringify({ 'created': moment(), 'data': data }))
    console.log('success create' + filename)
}

function findThumbnail(descFull) {
    // <img class="img-in-post" src="https://f.ptcdn.info/642/063/000/pqgvvokmjZYsnUCJtk3-o.jpg" data-image
    const startText = '<img class="img-in-post" src="'
    const endText = '" data-image'
    let i = descFull.search(startText)
    let j = descFull.search(endText)
    if (i != -1 && j != -1) {
        return descFull.substring(i + startText.length, j)
    } else {
        return ""
    }
}

function findCountryFromTags(tags) {
    for (tag of tags) {
        for (country of countriesListTH) {
            if (tag.includes(country)) {
                return countriesList[country]
            }
        }
    }
    return ""
}

function findDuration(title, desc) {
    let searchTexts = ['วัน', 'day']
    let numEng = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eigth', 'nine', 'ten', 'eleven', 'twelve', 'thirteen']
    let numTH = ['หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า', 'สิบ', 'สิบเอ็ด', 'สิบสอง', 'สิบสาม']
    let duration = ""

    const str = (title + desc)
    let foundIndex = 0
    let currentIndex = 0
    while (duration == "" && foundIndex != -1 && currentIndex < str.length) {
        foundIndex = str.substring(currentIndex).search(/วัน|day/i)
        // console.log('foundIndex:', foundIndex)
        // console.log('text',str.charAt(foundIndex+currentIndex),str.charAt(foundIndex+currentIndex+1))
        let i = currentIndex + foundIndex - 1
        // console.log("i", i)
        // console.log("si", str.charAt(i))
        let j = -1
        while (i >= foundIndex - 10 && i >= 0) {
            const s = str.substring(i, currentIndex + foundIndex).replace(/\s/g, '')
            // console.log("in while2")
            // console.log("s", s, "<<")
            if ((i >= foundIndex - 4 && !isNaN(s))) {
                // console.log("j in number", j)
                j = parseInt(s) - 1
                break
            } else if (numTH.includes(s) || numEng.includes(s)) {
                j = numTH.indexOf(s)
                break;
            }

            i--;
        }
        // console.log("j", j)

        if (j >= 0 && j < 3) duration = durationEnum.ONETHREE
        else if (j >= 3 && j < 6) duration = durationEnum.FOURSIX
        else if (j >= 6 && j < 9) duration = durationEnum.SEVENNINE
        else if (j >= 9 && j < 12) duration = durationEnum.TENTWELVE
        else if (j >= 12) duration = durationEnum.MORE

        if (duration != "")
            break

        currentIndex += ++foundIndex
        // console.log("ci", currentIndex)
    }
    return duration

}

function findSeason(title, desc) {
    let months1 = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
    let months2 = ['มค', 'กพ', 'มีค', 'เมย', 'พค', 'มิย', 'กค', 'สค', 'กย', 'ตค', 'พย', 'ธค']
    let months3 = ['ม.ค', 'ก.พ', 'มี.ค', 'เม.ย', 'พ.ค', 'มิ.ย', 'ก.ค', 'ส.ค', 'ก.ย', 'ต.ค', 'พ.ย', 'ธ.ค']
    let months4 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    let months5 = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


    let months = [...months1, ...months2, ...months3, ...months4].reduce((prev, cur) => prev + '|' + cur)
    let re = new RegExp(months, 'gi')

    // let months = months1.toString()+","+months2.toString()+","+months3.toString()
    // console.log("----",months)
    // months = months.replace(/\,/g,'|')
    // console.log(">>>>>",months)
    // let re = new RegExp(months,'gi')
    // console.log("<<<<<",re)

    let season = ""





    return season
}

const fetchDetail = async () => {
    const topicIDList = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json'))
    console.log(typeof topicIDList)


    for (const element of topicIDList) {
        let smartObject = {}
        let topicID = element.topicID
        try {
            const response = await axios.get('http://ptdev03.mikelab.net/kratooc/' + topicID)
            const detail = response.data._source

            smartObject.topicID = topicID
            smartObject.title = detail.title
            smartObject.desc = detail.desc
            smartObject.thumbnail = findThumbnail(detail.desc_full)
            smartObject.country = findCountryFromTags(element.tags)
            smartObject.duration = findDuration(detail.title, detail.desc)
            smartObject.period = ""
            smartObject.theme = ""
            smartObject.budget = ""
            smartObject.view = element.view
            smartObject.score = {
                view: element.view,
                emotionSum: detail.emotion.sum,
                commentLength: detail.comment_count,
                point: detail.point

            }
            smartObject.link = detail.permalink


        } catch (err) {
            console.log('cannot fetch ', topicID)
            console.log(err)
        }
    };

}



const fetchTest = async () => {
    let topicID = '38810472'
    let detail = {}
    try {
        const response = await axios.get('http://ptdev03.mikelab.net/kratooc/' + topicID)
        detail = response.data._source
        // console.log(detail)
        // console.log(durationEnum.ONETHREE)
        console.log(topicID, detail.title)
        // console.log(findDuration('day' + detail.title, detail.desc))
        console.log(findSeason(detail.title, detail.desc))

    } catch (err) {
        console.log('test -> cannot fetch ', topicID)
        console.log(err)
    }


}

fetchTest()
