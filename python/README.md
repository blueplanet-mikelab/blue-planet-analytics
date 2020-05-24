# Blueplanet project
![Imgur](https://i.imgur.com/qX4KCRY.jpg)

## Video Links
##### Project trailer: https://youtu.be/E7XD336SghY<br>
##### Project presentation: https://www.youtube.com/watch?v=gHh1ErghylY<br>

## Short description
This web application is developed in order to solve the difficulty of finding review posts/threads which are used as information for planning trips. At present, while planning a trip, Thai people always search for interesting travel reviews, especially the review threads of Pantip.com which are very popular in Thailand. However, not every post will match their needs. Sometimes, they have to read up to 10 threads, but just only one thread can be used. Therefore, our web application is classifying threads so that users are able to filter only the threads they want. Moreover, the application provides other services such as suggesting posts and creating your favorite triplist.

This project consist of 3 repositories
1. Front-end: https://gitlab.mikelab.net:65443/blueplanet/fontend is about the user interface.
2. Back-end: https://gitlab.mikelab.net:65443/blueplanet/backend is a bridge between front-end and database. It is used to send data from database to front-end and receive data from front-end to keep in database.
3. Analytic: https://gitlab.mikelab.net:65443/blueplanet/analytics (this repository) its work is prepare/classify data and push them into database. Please read the files explanation below for the objective of each file.

**After finish installation,** to play a web application, you need to execute back-end first by run command `nodemon server.js` on the back-end directory. Then, go to the front-end directory and run `yarn start`. There is no need to run **Analytic repository** to play the web application.

# Installation
##### Video Guide: [https://youtu.be/GQMlnH3kOjc](https://youtu.be/GQMlnH3kOjc)<br>


## 0) Prerequisites
Front-end: NodeJS<br>
Back-end: NodeJS<br>
Analysis: Python3.6+, MongoDB<br>

**useful link**
* [Python 3](https://www.python.org/downloads/)
* [Node.js 10](https://nodejs.org/en/download/)
* MongoDB version 3
  * [Redhat / CentOS](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-red-hat/)
  * [Ubuntu](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/)
  * [Windows](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/)
  * [macOS](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/)

## 1) Download database
upload the initial data via mongo console so you need to run mongo server and go to `mongo console` and run command as below. Moreover, these data files can be downloaded from [drive link](https://drive.google.com/open?id=1o32lGgDkFFnpxfMkUGmORJvJnJQb1h9L).
```bash
> load("/path/to/parent/directory/mongo_js/initialize/[filename].js")
```
Here is all commands for all data to download. 
```bash
> load("import_classified_thread_300.js")
> load("import_classified_thread_20200425.js")
> load("import_countries_list.js")
> load("import_favorites.js")
> load("import_recently_viewed.js")
> load("import_triplists.js")
``` 

## 2) Clone each project
Go to favor directory on your computer
```bash
$ git clone https://gitlab.mikelab.net:65443/blueplanet/fontend<br>
$ git clone https://gitlab.mikelab.net:65443/blueplanet/backend<br>
$ git clone https://gitlab.mikelab.net:65443/blueplanet/analytics<br>
```

## 3) Back-end installation (both on local and production)
from parent directory
```bash
$ cd backend/
```

install package using command `yarn` or `npm install`
```bash
$ yarn
```

download `serviceKeyAccount.json` and `.env` via [link](https://drive.google.com/drive/folders/1DeOhtd_30hqlwL3_cbPWbZNQRmR2YL61?usp=sharing) using .ku.th account and paste them on the parent directory.

start server
```bash
$ nodemon server.js
```

## 4) Front-end installation
from parent directory
```bash
$ cd fontend/
```

install package using command `yarn` or `npm install`
```bash
$ yarn
```

start server if on local use
```bash
$ yarn start
```

but on production your have to add a env
```bash
$ export REACT_APP_BACKEND_URL=mars.mikelab.net:30010<br>
```

and then start on production
```bash
$ yarn start:production
```

## 5) Analytics installation
from parent directory
```bash
$ cd analytics/
```

install required package (pip version must >10.0.0)
```bash
$ pip install --upgrade pip<br>
$ pip install -r package_requirements.txt<br>
$ pip install pythainlp<br>
```

using `python` or `python3` commands for running files. Read the exaplnation for the objective of each file and folder.
```bash
$ python3 [filename.py]
```

### directory and files explanation
**1. clicksteam/**<br>
contain `ranking.py` for ranking the top country by the number of threads which related to the country. The threads are considerd in each day (now it is not an automatic run) from each collection in `clicksteam` database.

**2. config/**<br>
config files of database and url

**3. utils/**<br>
contain lot of python files which provide lot of `necessary functions`

**4. naiveBayes-mmscale-interval-090320/ (one of the fail version)**<br>
- all steps from create text -> clean text -> TF-IDF -> Naive Bayes Classification -> prediction
- The `trained data` consist of only threads which `have only one theme`.
- In the TF-IDF step, it uses the `tf-idf` score for cutting words that have a low score.
- In Naive Bayes classification, there is only one model to predict multiple themes of each thread.
- But the results are unacceptable.
- contain `train.py` which the main file for execution

**5. nb-mmscale-interval-yesno-230320/ (the lastest version)**<br>
- all steps from create text -> clean text -> TF-IDF -> Naive Bayes Classification -> prediction results -> measurements.
- The `trained data` consist of only threads which `have only one theme`.
- In the TF-IDF step, it uses the `idf` score for cutting words that have a low score.
- In Naive Bayes classification, there are models of each theme and predict the theme to be yes or no. So, to create the model, trained threads(data) with one theme of the current considered theme will be 'yes' and others are 'no'. For example, the current consider theme is 'Mountain'. The threads with one theme and that theme is 'Mountain' will be the 'yes' class and The threads with one theme and that theme is not 'Mountain' will be the 'no' class. These are X_train and Y_train data.
- Using the Jaccard Similarity Index to measure the similarity between trained dataset and predicted dataset.
- contain `train.py` which the main file for execution
- contain many folders named `[theme]-idf-new` which keep model files.

**6. classification-accuracy.py**<br>
aim to calculate similarity of 304 threads between classify manually and classify by program. This file writes `checked_300threads.json` and `accuracy_300threads.json`.

**7. checked_300threads.json**<br>
the result of chacking and calculating similarity of 304 threads between classify manually and classify by program.

**8. accuracy_300threads.json**<br>
summary measurements of 304 threads which are classified manually.

**9. co-occurrenceTest.py**<br>
learn and try co-occurrence.

**10. countriesListSorted.json**<br>
A list contain all countries's information around the world which are sorted by country code.

**11. labeledThreadsbyHand_v2.csv**<br>
The data of threads are classified manually (by project's members).

**12. classificationByPattern.py**<br>
The main file of threads classification.

**13. scheduleClassify.py**<br>
is used to automatically call a classification function every day for data updating.
