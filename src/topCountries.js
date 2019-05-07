//sort top coutries from exist tags

const fs = require('fs')
const path = require('path')
const db = require('monk')(process.env.MONGODB_URI,{authSource:'admin'})
// const db = require('monk')('localhost/pantip-blueplanet')
const moment = require('moment')
var filePath = path.join(__dirname, '/json/counting/combined/tagsTotalCount.json');
// var filePath = path.join(__dirname, '/json/tc/tcCount-blueplanet-20181112.json');
let topCountries = []

//TODO plus score in the country that find city
let japanCity = ['ประเทศญี่ปุ่น', 'โตเกียว', 'โอซาก้า', 'คันไซ', 'เที่ยวญี่ปุ่น']
let koreanCity = ['ประเทศเกาหลีใต้', 'โซล', 'สถานที่ท่องเที่ยวเกาหลี']
let taiwanCity = ['ไต้หวัน', 'ไทเป']
let finlandCity = ['ประเทศฟินแลนด์', 'เฮลซิงกิ']
let napaiCity = ['ประเทศเนปาล', 'กาฐมาณฑุ']
let omanCity = ['ประเทศโอมาน', 'มัสกัต']
let luxembourgCity = ['ประเทศลักเซมเบิร์ก', 'ลักเซมเบิร์ก']
let maxicoCity = ['ประเทศเม็กซิโก', 'เม็กซิโกซิตี']
let denmarkCity = ['ประเทศเดนมาร์ก', 'โคเปนเฮเกน']
let slovakiaCity = ['ประเทศสโลวาเกีย', 'บราติสลาวา']
let portugalCity = ['ประเทศโปรตุเกส', 'ลิสบอน']


fs.readFile(filePath, async function (err, data) {
    if (!err) {
        // console.log('received data: ' + data);
        let tagsArray = JSON.parse(data)
        // console.log(tagsArray)
        tagsArray.forEach(function (item) {
            // console.log(item)
            let tag = item['tags']
            // console.log(tag)
            if (tag.startsWith('ประเทศ') || tag === 'ฮ่องกง' || tag === 'ไต้หวัน' || tag === 'นครรัฐวาติกัน') {
                topCountries.push(item)
            }
        })
        

        // Add country in English
        let countriesList = JSON.parse(fs.readFileSync("./json/countries-list-th-eng.json")) //Object
        let countriesListTH = Object.keys(countriesList)
        topCountries.forEach(function (item){
            topCountry = item['tags']
            
            for(var country of countriesListTH) {
                if(topCountry.includes(country)){
                    item.countryEng = countriesList[country]
                    break;
                }
            }
        })

        // console.log(topCountries)

        let created = moment().format()
        console.log(">>>>>>", created)
        // Add to mongo
        await db.get('topCountries').insert({createdDate: created, topCountries: topCountries})
            .then(result => console.log(result))
            .then(() => db.close())

        // create JSON file
        // let foldername = './json/';
        // fs.writeFileSync(foldername + 'topCoutries.json', JSON.stringify({createdDate: created, topCountries: topCountries}))
        // console.log('success create topCoutries.json')
    
    } else {
        console.log(err);
    }
});