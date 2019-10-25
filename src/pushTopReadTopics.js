const db = require('monk')(process.env.MONGODB_URI, { authSource: 'admin' })
const fs = require('fs')

const items = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json'))
console.log(items.length)

db.get('topReadTopics').insert(items)
  .then(result => { console.log('inserted', result.length); db.close() })
  .catch(err => console.log('error to insert', err))