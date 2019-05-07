const db = require('monk')('mikestd:mikestd1q2w3e4r@mars.mikelab.net:27017/blueplanet_project', { authSource: 'admin' })
const fs = require('fs')

const items = JSON.parse(fs.readFileSync('./json/readTopics/combined/totalReadTopicsModel.json'))
console.log(items.length)

db.get('topReadTopics').insert(items)
  .then(result => { console.log('inserted', result.length); db.close() })
  .catch(err => console.log('error to insert', err))