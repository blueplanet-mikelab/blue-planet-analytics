import schedule
import time
import sys
from datetime import datetime as dt, timedelta
 
from classificationByPattern import classifyByPttern


def job():
    now = dt.now()
    start = time.time()
    print("start classification at %s" % now)
    print("--------------------------")

    try:
        print("-----| Start classificationByPattern.py |------")
        classifyByPttern()
        print("-----| Done classificationByPattern.py |------")
    except:
        print("!!!!!!!!!| Error: classificationByPattern.py |!!!!!!!!!!")

    print("==========================")
    print("finish classification in %s at %s" % (time.time() - start, dt.now()))

def jobtest():
    print("hello %s", dt.now())


print("---- Hello Aom Mai Ben Blueplan -----")
print("---- start schedualing -----")
# schedule.every(1).minutes.do(jobtest)

schedule.every().day.at("00:01").do(job)

while 1:
    schedule.run_pending()
    time.sleep(1)