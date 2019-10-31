// for using LDA technique with topReadTopicsModel

const fs = require('fs');
const lda = require('lda');
const axios = require('axios')
let text = ""
let errorFetchCount = 0

const topicIDList = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json'))
console.log(topicIDList.length)

const fetchDetail = async () => {
    // Example text.
    // let text = 'Cats are small. Dogs are big. Cats like to chase mice. Dogs like to eat bones.';

    for (i = 0; i < 50; i++) {
        let topicID = topicIDList[i].topicID
        console.log(i, topicID, ' fetching')
        await axios.get('http://ptdev03.mikelab.net/kratooc/' + topicID)
            .then(response => {
                const detail = response.data._source
                // console.log(detail.desc)
                text += detail.desc
            })
            .catch(err => {
                console.log(topicID, ' error to fetch')
                errorFetchCount += 1
            })

    }

    calculateLDA()
}

fetchDetail()

function calculateLDA() {
    console.log('err count: ', errorFetchCount)
    console.log('text length: ', text.length)
    console.log('some text: ', text.substring(0, 10000))
    console.log('start LDA')

    // Extract sentences.
    let documents = text.match(/[^\s]+[\s]+/g);

    // Run LDA to get terms for 2 topics (5 terms each).
    let result = lda(documents, 10, 20);

    console.log('lda finish')
    console.log(result)

    // For each topic.
    let sum = 0
    for (var i in result) {
        var row = result[i];
        console.log('Topic ' + (parseInt(i) + 1));
        let sumEachProp = 0
        row.map(obj => sumEachProp += obj.probability)
        sum += sumEachProp
        // For each term.
        for (var j in row) {
            var term = row[j];
            console.log(term.term + ' (' + term.probability + '%)');
        }

        console.log('sum prop of this topic: ', sumEachProp);
        console.log('')
    }
    console.log('sum all prop = ', sum)
}

