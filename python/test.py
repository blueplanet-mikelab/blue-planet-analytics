import json
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