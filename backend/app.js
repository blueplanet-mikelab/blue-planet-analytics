const express = require('express')
const app = express()
const port = 8000
const monk = require('monk')
const config = require('./config.json')
const configDB = config.pantip-ds
const dburl = `${configDB.username}:${configDB.password}@${configDB.host}:27017/${configDB.db}`;
const db = monk(dburl,{authSource:'dev'});
const bodyParser = require('body-parser');
db.then(() => { console.log('Connected successfully to mongo')})
const treads_col = db.get('classified_thread_251119') //TODO

function selectSorting(sortby){
    if(sortby=="upvoted") return {"totalVote":-1}
    else if(sortby=="shared") return {"created_at":-1}  //TODO
    else if(sortby=="popular") return {"popularity":-1} 
    else if(sortby=="newest") return {"created_at":-1}
    else if(sortby=="oldest") return {"created_at":1}
    else return null
}

app.use(bodyParser.json());

app.get('/', function(req,res){
    res.send("Hello World*****")
})

app.get('/forumlist/all/:sortby/:page', function(req, res){
    // console.log(__dir name + '/index.html')
    // res.sendFile(__dirname + '/index.html');
    res.setHeader('Content-Type', 'application/json');
    console.log(req.params, req.params.sortby, req.params.page, parseInt(req.params.page))
    var sortby = req.params.sortby;
    var result_page = parseInt(req.params.page) - 1;
    var result_num = 10
    var skip_num = result_num * result_page
    sorting = selectSorting(sortby)
    console.log(sortby, result_page, skip_num, sorting)
    if(sorting == null){
        res.status(422);
        res.send('sort by type is not invalid');
    } else{
        treads_col.find({}, {sort: sorting, skip: skip_num, limit: result_num}).then((doc) => {
            console.log(doc)
            res.send(doc);
        })
    }

});

app.post('/forumlist/conditions', function(req, res){
    console.log(req.body)
    result_per_page = 10

    var type = req.body.type
    var countries = req.body.countries; //array of string ["Thailand","Singapore"]
    var c_filter = []
    if(countries != null){
        countries.forEach(country => {
            c_filter.push( { "$eq": [ "$$country.nameEnglish", toString(country) ] } )
        })
    }

    var duration = req.body.duration; //array of string ["1-3Days", "4-6Days", "7-9Days","10-12Days","Morethan12Days"]
    d_filter = []
    if(duration != null){
        duration.array.forEach(label => {
            parts = label.replace(/\s+/, "").match(/(than|\d+)-*(\d+)Days/)
            if(parts[1]=="than"){
                d_filter.push( { "$and": [ {"$gt":["$duration.days", 12]} ] } )
            }else{
                d_filter.push( { "$and": [ {"$gte":["$duration.days", parts[1]]},{"$lte":["$duration.days", parts[2]]} ] } )
            }
        });
    }else{ //suggest
        d_filter.push( { "$eq":["$duration.days", 0]} )
    }

    var month = req.body.month; //array of string ["January", "September"]
    m_filter = [] //TODO if month==null retrurn all
    month.forEach(mon => {
        m_filter.push( { "$eq": [ "$$mon", mon ] } )
    })

    var themes = req.body.theme; //array of string ["Mountain","Sea"]
    t_filter = [] //TODO if theme==null not filter theme if theme == etc select theme:[]
    themes.forEach(theme => {
        t_filter.push( { $eq: [ "$$theme.theme", theme ] } )
    })
    var budget_min = parseInt(req.body.budgetMin);
    var budget_max = parseInt(req.body.budgetMax);
    var result_page = parseInt(req.body.resultPage);
    var sortby = toString(req.body.sortby);
    pipeline = [
        {
            $project: {
                "topic_id" : 1,
                "title" : 1,
                "thumbnail" : 1,
                "countries" : 1,
                "duration" : 1,
                "month" : 1,
                "theme" : 1,
                "budget" : 1,
                "totalView" : 1,
                "totalVote" : 1,
                "totalComment" : 1,
                "popularity" : 1,
                "created_at" : 1,
                "c_filter" : {
                    $filter:{
                        input: "$countries",
                        as: "country",
                        cond:{ $or: c_filter}
                    }
                },
                "d_filter" : { $or: d_filter },
                "m_filter" : {
                    $filter:{
                        input: "$month",
                        as: "mon",
                        cond:{ $or: m_filter }
                    }
                }, 
                "t_filter" : {
                    $filter:{
                        input: "$theme",
                        as: "theme",
                        cond:{ $or: t_filter }
                    }
                },
                "b_filter" : { $or: [
                            { $and: [ {$gte:["$budget", budget_min ]}, {$lte:["$budget", budget_max ]} ] },
                            { $eq: ["$budget", -1] }
                ]},
            }
        },
        {
            $match: { $and: [
                {"c_filter": {$ne: []}},
                {"d_filter": {$eq: true}},
                {"m_filter": {$ne: []}},
                {"t_filter": {$ne: []}},
                {"b_filter": {$eq: true}}
            ]}
        },{ 
            $sort : selectSorting(sortby) 
        },
        { 
            $project: {
                "c_filter": 0,
                "d_filter": 0,
                "m_filter": 0,
                "t_filter": 0,
                "b_filter": 0
            }
        },
        {   $skip : 10*result_page },
        {   $limit : 10 }
        // ,{ $count: "count" }
    ]
    treads_col.aggregate(pipeline).then((doc) => {
        // console.log(doc)
        res.send(doc);
    })
    
});

app.listen(port, () => console.log(`Example app listening on port ${port}!`))