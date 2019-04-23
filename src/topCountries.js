const fs = require('fs')
const path = require('path')
const db = require('monk')('localhost/pantip-blueplanet')
const moment = require('moment')
var filePath = path.join(__dirname, '/json/counting/combined/tagsTotalCount.json');
// var filePath = path.join(__dirname, '/json/tc/tcCount-blueplanet-20181112.json');
let topCountries = []

//TODO plus score in the country that find city
let japanCity = ['ประเทศญี่ปุ่น','โตเกียว','โอซาก้า','คันไซ']
let koreanCity = ['ประเทศเกาหลีใต้','โซล','สถานที่ท่องเที่ยวเกาหลี']
let taiwanCity = ['ไต้หวัน','ไทเป']
let finlandCity = ['ประเทศฟินแลนด์','เฮลซิงกิ']
let napaiCity = ['ประเทศเนปาล','กาฐมาณฑุ']
let omanCity = ['ประเทศโอมาน','มัสกัต']
let luxembourgCity = ['ประเทศลักเซมเบิร์ก','ลักเซมเบิร์ก']
let maxicoCity = ['ประเทศเม็กซิโก','เม็กซิโกซิตี']
let denmarkCity = ['ประเทศเดนมาร์ก','โคเปนเฮเกน']
let slovakiaCity = ['ประเทศสโลวาเกีย','บราติสลาวา']
let portugalCity = ['ประเทศโปรตุเกส','ลิสบอน']


fs.readFile(filePath, async function (err, data) {
    if (!err) {
        // console.log('received data: ' + data);
        let tagsArray = JSON.parse(data)
        // console.log(tagsArray)
        tagsArray.forEach(function(item){
            // console.log(item)
            let tag = item['tags']
            // console.log(tag)
            if(tag.startsWith('ประเทศ') || tag === 'ฮ่องกง' || tag === 'ไต้หวัน' || tag === 'นครรัฐวาติกัน'){
                topCountries.push(item)
            }
        })
        console.log(topCountries)
        await db.get('TopCountries').insert({createdDate: moment(), topCountries: JSON.stringify(topCountries)})
        .then(result => console.log(result))
        // db.close()
    } else {
        console.log(err);
    }
});