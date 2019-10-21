import csv
import pprint

with open('./labeledThreadsbyHand.csv', 'r', encoding="utf8") as f:
    threads = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

# pprint.pprint(threads)
print(threads[0]['Theme'].split(','))

#TODO retrieve title+destription+comment
#TODO to mongo
#TODO TFIDF
#TODO Vector