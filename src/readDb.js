const db = require('monk')('localhost/pantip-blueplanet')

db.get('TopCountries').find()
.then(res => console.log(JSON.parse(res[0].topCountries)))
.then(() => db.close())
