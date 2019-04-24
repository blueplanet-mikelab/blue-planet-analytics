// conbine 

const fs = require('fs');
var path = require('path');
const moment = require('moment')

function createReport(data, filename, dir) {
    data = data.sort(function (obj1, obj2) { return obj2.view - obj1.view })
    fs.writeFileSync(dir + filename, JSON.stringify({'created': moment(), 'data': data}))
    console.log('success create' + filename)
}

function combine(folderPath, targetKey, targetValue) {
    let fullPath = path.join(__dirname, folderPath)
    let files = fs.readdirSync(fullPath)
    let totalCount = {};
    for (const file of files) {
        console.log(file)
        let topicData = fs.readFileSync(folderPath + file)
        topicCount = JSON.parse(topicData);

        Object.values(topicCount).forEach(item => { //each object in array
            if (Object.keys(item).includes(targetKey)) {
                let topic_id = item[targetKey]
                if (totalCount[topic_id] == undefined) {
                    totalCount[topic_id] = item
                } else {
                    totalCount[topic_id][targetValue] += item[targetValue]
                }
            }
        })
    }
    return Object.values(totalCount)
}

createReport(combine('./json/readTopics/data/', 'topic_id', 'view'), 'totalReadTopics.json', './json/readTopics/combined/')
// createReport(combine('./test/readTopics/data/', 'topic_id', 'view'), 'totalReadTopics.json', './test/readTopics/combined/')