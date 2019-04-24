// count tags, event, tc, and topic_id then create count file for 1 day per file 

const fs = require('fs');
const zlib = require('zlib');
const readline = require('readline');
const path = require('path');
const directoryPath = path.join('/amazon_data/blueplanet');
// const directoryPath = path.join(__dirname, 'testdata');
let tagsCount = {};
let tcCount = {};
let eventCount = {};
let topicidCount = {};
const targetKeys = ['tags', 'event', 'tc', 'topic_id'];

const main = async () => {
    const files = fs.readdirSync(directoryPath)
    for (const file of files) {
        tagsCount = {};
        tcCount = {};
        eventCount = {};
        topicidCount = {};
        console.log(file)
        await readgzip(file);

        tagsCount = Object.keys(tagsCount).map(key => ({ tags: key, count: tagsCount[key] }))
        tcCount = Object.keys(tcCount).map(key => ({ tc: key, count: tcCount[key] }))
        eventCount = Object.keys(eventCount).map(key => ({ event: key, count: eventCount[key] }))
        topicidCount = Object.keys(topicidCount).map(key => ({ topicid: key, count: topicidCount[key] }))

        // parallel
        // await Promise.all(files.map(file => readgzip(file)))
        createReport(file);
    }
}

main()

async function readgzip(filename) {
    let gzFileInput = fs.createReadStream('/amazon_data/blueplanet/'+filename);
    // const gzFileInput = fs.createReadStream("./testdata/" + filename);
    // console.log(filename)
    let gunzip = zlib.createGunzip();

    const interface = readline.createInterface({
        input: gunzip,
    })
    await new Promise((resolve, reject) => {
        // let lineCount = 0;
        let datalist = []

        interface.on('line', line => {
            // lineCount++;
            // console.log("-----------------------------------------")
            // console.log(line)
            datalist.push(JSON.parse(line))
        })
        interface.on('close', () => {
            // console.log({ lineCount });
            // count target data

            datalist.forEach(function (item) {
                // 'tags'
                key = targetKeys[0]
                if (Object.keys(item).includes(targetKeys[0])) {
                    Object.values(item[targetKeys[0]]).forEach(function (tag) {
                        tagsCount[tag] = tagsCount[tag] != undefined ? tagsCount[tag] + 1 : 1
                    });
                }
                //'event'
                key = targetKeys[1]
                if (Object.keys(item).includes(key)) {
                    value = item[key]
                    eventCount[value] = eventCount[value] != undefined ? eventCount[value] + 1 : 1
                }
                //'tc'
                key = targetKeys[2]
                if (Object.keys(item).includes(key)) {
                    value = item[key]
                    tcCount[value] = tcCount[value] != undefined ? tcCount[value] + 1 : 1
                }
                //'topic_id'
                key = targetKeys[3]
                if (Object.keys(item).includes(key)) {
                    value = item[key]
                    topicidCount[value] = topicidCount[value] != undefined ? topicidCount[value] + 1 : 1
                }

                // targetKeys.forEach(function (key) {
                //     if (Object.keys(item).includes(key)) {
                //         switch (key) {
                //             case 'tags':
                //                 Object.values(item['tags']).forEach(function (tag) {
                //                     tagsCount[tag] = tagsCount[tag] != undefined ? tagsCount[tag] + 1 : 1
                //                 });
                //                 break;
                //             case 'event':
                //                 value = item[key]
                //                 eventCount[value] = eventCount[value] != undefined ? eventCount[value] + 1 : 1
                //                 break;
                //             case 'tc':
                //                 value = item[key]
                //                 tcCount[value] = tcCount[value] != undefined ? tcCount[value] + 1 : 1
                //                 break;
                //             case 'topic_id':
                //                 value = item[key]
                //                 topicidCount[value] = topicidCount[value] != undefined ? topicidCount[value] + 1 : 1
                //                 break;
                //             default:
                //                 console.log("key not found")
                //         }
                //     }
                // })
            });

            console.log("complete datalist")
            // console.log(count)

            // analyse
            // users_num = Object.keys(tcCount[value]).length - 1
            // console.log("The number of user: ",users_num)
            // console.log("Events/Users = ",lineCount/users_num)
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

function createReport(file) {
    let filename = file.substring(0, file.length - 3);
    let foldername = '../json/counting/';
    // create txtfile
    tagsCount = tagsCount.sort(function (obj1, obj2) { return obj2.count - obj1.count })
    fs.writeFileSync(foldername + 'tags/tagsCount-' + filename + '.json', JSON.stringify(tagsCount))
    console.log('success create tagsCount-' + filename + '.json')

    fs.writeFileSync(foldername + 'event/eventCount-' + filename + '.json', JSON.stringify(eventCount))
    console.log('success create eventCount-' + filename + '.json')

    fs.writeFileSync(foldername + 'tc/tcCount-' + filename + '.json', JSON.stringify(tcCount))
    console.log('success create tcCount-' + filename + '.json')

    topicidCount = topicidCount.sort(function (obj1, obj2) { return obj2.count - obj1.count })
    fs.writeFileSync(foldername + 'topicid/topicidCount-' + filename + '.json', JSON.stringify(topicidCount))
    console.log('success create topicidCount-' + filename + '.json')
}