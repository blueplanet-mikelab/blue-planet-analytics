// conbine 

const fs = require('fs');
var path = require('path');
const moment = require('moment')
const db = require('monk')('localhost/pantip-blueplanet')

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
        // break;
    }
    return Object.values(totalCount)
}
let countedArray = combine('./json/readTopics/data/', 'topic_id', 'view')
// let countedArray = combine('./test/readTopics/data/', 'topic_id', 'view')

let created = moment().format()
let items = countedArray.map(item => ({ createdDate: created, topicID: item.topic_id, tags: item.tags, view: item.view, mid: item.mid, tc: item.tc }))
items = items.sort(function (obj1, obj2) { return obj2.view - obj1.view })

// Create file
function createReport(data,dirname) {
    // data = data.sort(function (obj1, obj2) { return obj2.count - obj1.count })
    fs.writeFile(dirname, items)
    console.log('success create' + dirname)
}
createReport(items,'./json/readTopics/combined/totalReadTopicsModel.json')
console.log('success create file model')


// Add to mongo
// const topicIDList = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json')).data.map(topicID => ({ ...topicID, createdDate: moment().format() }))
// db.get('topicTest').insert(topicIDList)
//     .then(result => {
//         console.log('inserted')
//         db.close()
//     })








