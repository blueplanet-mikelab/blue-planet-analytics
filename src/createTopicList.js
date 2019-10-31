const db = require('monk')(process.env.MONGODB_URI, { authSource: 'admin' })
const fs = require('fs');

db.get('topReadTopics').find({}, { 'topicID': 1 })
    .then(res => {
        // console.log(res)
        // console.log(JSON.parse(res[0].topicID))

        let array = []
        // create file for aom
        for (i = 0; i < 900; i++) {
            array.push(JSON.parse(res[i].topicID))
            if (i == 299) {
                fs.writeFileSync('./json/topicForClassify/Aom.json', JSON.stringify(array))
                console.log('success create Aom topics files')
                array.length = 0
            } else if (i == 599) {
                fs.writeFileSync('./json/topicForClassify/Mai.json', JSON.stringify(array))
                console.log('success create Mai topics files')
                array.length = 0
            } else if (i == 899) {
                fs.writeFileSync('./json/topicForClassify/Ben.json', JSON.stringify(array))
                console.log('success create Ben topics files')
                array.length = 0
            }
        }
        db.close()
    })
    .catch(err => {
        console.log(err)
        db.close()
    })
