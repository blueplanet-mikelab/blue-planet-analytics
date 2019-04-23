// conbine result of counted file as combined floder

const fs = require('fs');
var path = require('path');

function createReport(data,filename,dir) {
    data = data.sort(function (obj1, obj2) { return obj2.count - obj1.count })
    fs.writeFileSync(dir+filename, JSON.stringify(data))
    console.log('success create' + filename)
}

function combine(folderPath,targetKey,targetValue) {
    let tagsPath = path.join(__dirname, folderPath)
    let files = fs.readdirSync(tagsPath)
    let totalCount = {}
    for (const file of files) {
        console.log(file)
        let tagsData = fs.readFileSync(folderPath + file)
        tagsCount = JSON.parse(tagsData);

        tagsCount.forEach(item => { //each object in array
            if(Object.keys(item).includes(targetKey)) {
                let tag = item[targetKey]
                totalCount[tag] = totalCount[tag] != undefined ? totalCount[tag] + item[targetValue] : item[targetValue]
            }
        })
    }
    totalCount = Object.keys(totalCount).map(key => ({ [targetKey]: key, [targetValue]: totalCount[key] }))
    return totalCount 
}

// tags
createReport(combine('../json/counting/tags/','tags','count'), 'tagsTotalCount.json','json/combined/')
// event
createReport(combine('../json/counting/event/','event','count'), 'eventTotalCount.json','json/combined/')
// topicid
createReport(combine('../json/counting/topicid/','topicid','count'), 'topicidTotalCount.json','json/combined/')
// tc
createReport(combine('../json/counting/tc/','tc','count'), 'tcTotalCount.json','json/combined/')


// createReport(combineTagsCount(), 'tagsTotalCount.json','json/combined/')
// console.log(combineTagsCount())