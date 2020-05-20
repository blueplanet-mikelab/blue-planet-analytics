import schedule
import threading
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


# create jop in parallel
def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


print("---- Hello Aom Mai Ben Blueplan -----")
print("---- start schedualing -----")

schedule.every().day.at("00:01").do(run_threaded, job)

while 1:
    schedule.run_pending()
    time.sleep(1)

#------------------------------------------
#for parallel -> https://schedule.readthedocs.io/en/stable/faq.html