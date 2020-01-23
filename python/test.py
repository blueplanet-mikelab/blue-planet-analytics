import json, csv, pprint, copy
import pymongo

dir_path = './naiveBayes-maxminscale/'

with open('./config/database.json') as json_data_file:
    dbConfig = json.load(json_data_file)
    dsdb = dbConfig["mikelab"]
    client = pymongo.MongoClient(dsdb["host"],
                                27017,
                                username=dsdb["username"],
                                password=dsdb["password"],
                                authSource=dsdb["authSource"] )
    db = client[dsdb["db"]]

def readModel():
    with open(dir_path+'5-themeModels-maxmin-interval.json') as json_data_file:
        print('read data')
        theme_model = json.load(json_data_file)
        print('finish reading data, start ')

        model_col = db["naive_bayes_maxminscale"]
        # modelToInsert = [ 
        #     {'theme_name':key, 
        #     'topic_ids':themeDetail['topic_ids'], 
        #     'words_count':themeDetail['words_count']} 
        #     for key, themeDetail in theme_model.items()]

        for key, themeDetail in theme_model.items():
            result = model_col.insert_one(
                {'theme_name':key, 
                'topic_ids':themeDetail['topic_ids'], 
                'words_count':themeDetail['words_count']} 
            )

        # result = model_col.insert_many(modelToInsert)
        
        # topic_length = { theme:len(model['topic_ids']) for theme,model in theme_model.items()}
        # print(topic_length)

if __name__ == "__main__":
    # allThemeList = {
    #     'Mountain':['Mountain'], 'Waterfall':['Waterfall'], 
    #     'Sea':['Sea'], 
    #     'Religion':['Religion'], 
    #     'Historical':['Historical'], 
    #     'Entertainment':['Museum','Zoo','Amusement','Aquariam','Casino','Adventure'], 
    #     'Festival':['Festival','Exhibition'], 
    #     'Eating':['Eating'],
    #     'NightLifeStyle':['NightFood', 'Pub', 'Bar'], 
    #     'Photography':['Photography'],
    #     'Sightseeing':['Sightseeing']
    # }
    allThemeList = {
        'Mountain':['Mountain','Waterfall'], 
        'Sea':['Sea'], 
        'Religion':['Religion'], 
        'Historical':['Historical'], 
        'Entertainment':['Museum','Zoo','Amusement','Aquariam','Casino','Adventure','Festival','Exhibition'], 
        'Eating':['Eating','NightFood', 'Pub', 'Bar'], 
        'Photography':['Photography'],
        'Sightseeing':['Sightseeing']
    }
    #! 0. read csv -> threadsList
    with open('./labeledThreadsbyHand_v2.csv', 'r', encoding="utf8") as f:
        threadsList = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        threadTheme = {t["TopicID"]:t["Theme"].replace(" ","").split(",") for t in threadsList}
    
    # count = {
    #     'Mountain':0, 
    #     'Waterfall':0, 
    #     'Sea':0, 
    #     'Religion':0, 
    #     'Historical':0, 
    #     'Entertainment':0, 
    #     'Festival':0, 
    #     'Eating':0,
    #     'NightLifeStyle':0, 
    #     'Photography':0,
    #     'Sightseeing':0
    # }
    count = {
        'Mountain':0, 
        'Sea':0, 
        'Religion':0, 
        'Historical':0, 
        'Entertainment':0, 
        'Eating':0,
        'Photography':0,
        'Sightseeing':0
    }
    counts = {}
    for i in range(1,6,1):
        counts[str(i)] = copy.deepcopy(count)

    # pprint.pprint(counts)

    for thead, themes in threadTheme.items():
        for idx, theme in enumerate(allThemeList):
            # print("current Theme:", theme)
            memberTheme = allThemeList[theme]
            #add topic id
            if any([mt in themes for mt in memberTheme]):
                # print("append:",theme)
                counts[str(len(themes))][theme] = counts[str(len(themes))][theme]+1
            else:
                # print("skip")
                continue

    pprint.pprint(counts)
