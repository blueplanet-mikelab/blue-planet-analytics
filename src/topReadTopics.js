const fs = require('fs');
const zlib = require('zlib');
const readline = require('readline');
const path = require('path');
const directoryPath = path.join('/home/vittunyuta/blueplanet');
// const directoryPath = path.join(__dirname, 'testdata');
let topicidCount = {}

const main = async () => {
    const files = fs.readdirSync(directoryPath)
    for (const file of files) {
        // clear topicidCount before read
        topicidCount = {}
        
        await readgzip(file);
        
        // parallel
        // await Promise.all(files.map(file => readgzip(file)))
        
        createReport(file);
    }
}

main()

async function readgzip(filename) {
    let gzFileInput = fs.createReadStream('/home/vittunyuta/blueplanet/'+filename);
    // const gzFileInput = fs.createReadStream("./testdata/" + filename);
    console.log(filename)
    let gunzip = zlib.createGunzip();

    const interface = readline.createInterface({
        input: gunzip,
    })

    await new Promise((resolve, reject) => {
        let datalist = [] //all data
        interface.on('line', line => {
            datalist.push(JSON.parse(line))
        })
        interface.on('close', () => {
            datalist.forEach(function (obj) {
                
                usedkey = ['topic_id','tags','event','mid','tc']
                // if (isIncludeKeys(usedkey,obj) && obj[usedkey[2]]==="start") {               
                
                if (Object.keys(obj).includes('topic_id') && Object.keys(obj).includes('tags') 
                && Object.keys(obj).includes('event') && Object.keys(obj).includes('mid') 
                && Object.keys(obj).includes('tc') && obj[usedkey[2]]==="start" && !(obj[usedkey[0]].toString()==="0")) {
                    //prepare
                    topic_id = obj[usedkey[0]].toString()
                    tags = Object.values(obj[usedkey[1]])
                    mid = obj[usedkey[3]].toString()
                    tc = obj[usedkey[4]].toString()
                    // console.log(topic_id,tags,mid,tc)
                    // check
                    if(topicidCount[topic_id] == undefined){
                        topicidCount[topic_id] = {
                            'topic_id' : topic_id,
                            'tags' : tags,
                            'view' : 1,
                            'mid' : [mid]
                        }
                        topicidCount[topic_id]['tc'] = mid == "0" ? [tc] : []
                    } else {
                        if(!topicidCount[topic_id]['mid'].includes(mid)){
                            topicidCount[topic_id]['view'] += 1
                            topicidCount[topic_id]['mid'].push(mid)
                        }
                        if(mid == "0" && !topicidCount[topic_id]['tc'].includes(tc)){
                            topicidCount[topic_id]['view'] += 1
                            topicidCount[topic_id]['tc'].push(tc)
                        }
                        
                    }
                }
            });
            // console.log(topicidCount)
            console.log(Object.keys(topicidCount).length)
            resolve()
        });

        gzFileInput.on('data', function (data) {
            gunzip.write(data);
        });
        gzFileInput.on('end', function () {
            gunzip.end();
        });
    })
}

// function isIncludeKeys(keysArray, obj){
//     keysArray.forEach(function(key) {
//         if(!Object.keys(obj).includes(key)){
//             return false
//         }
//     })
//     return true
// }

function createReport(file) {
    let filename = file.substring(0, file.length - 3);
    let foldername = './json/readTopics/data';
    // let foldername = './test/readTopics/data/';
    // create txtfile
    fs.writeFileSync(foldername + 'topicidCount-' + filename + '.json', JSON.stringify(topicidCount))
    console.log('success create topicidCount-' + filename + '.json')
}