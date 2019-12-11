# Routes Documents
### 1. /forumlist/all/:sortby/:page
response all docs as sorted and arrange by the number of the page

**Request:** no body request but there are 2 params `sortby` and `page`<br>
**Response:**

Header
- 'Content-Type' : 'application/json'

Body: list of documents
- "_id" : ObjectId("..."),
- "topic_id" : 39xxxxxx.0,
- "title" : "Title",
- "thumbnail" : "https://xxxx.jpg",
- "countries" : [ 
        {
    - "country" : "TW",
    - "latitude" : 23.69781,
    - "longitude" : 120.960515,
    - "nameEnglish" : "Taiwan",
    - "nameThai" : [  "ไต้หวัน" ] <br>
        }, ....
    ],
- "duration" : {
    - "days" : 4,
    - "label" : "4 Days"
    },
- "month" : [ "August", ... ],
- "season" : "",
- "theme" : [ 
        { //at most 4 themes
    - "theme" : "Eatting",
    - "count" : 96 <br>
        }, 
        ..
    ],
- "budget" : 9423,
- "totalView" : 5752,
- "totalVote" : 1,
- "totalComment" : 10,
- "popularity" : 56.4780824434962,
- "created_at" : ISODate("2019-08-15T12:48:08.366Z")

### 2. /forumlist/filter
selecting docs using filter from the web
**Request:** <br>
Header
- 'Content-Type' : 'application/json'

Body:
- countries: ["Taiwan", "Thailand"]
- duration: ["1-3Days", "4-6Days", "7-9Days","10-12Days","Morethan12Days"]
- month: ["August", "October"]
- theme: ["Mountain","Historical","Sightseeing"]
- budget_min: 0
- budget_max: 10000
- result_page: 1 (start from 1)
- sortby: 4 values available
    - upvoted
    - popular
    - newest
    - oldest


**Response:**
the same as the first routes (just have more filter conditions)