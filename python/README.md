# Blueplanet project installation
This project consist of 3 repositories
1. Front-end: https://gitlab.mikelab.net:65443/blueplanet/fontend
2. Back-end: https://gitlab.mikelab.net:65443/blueplanet/backend
3. Analytic: https://gitlab.mikelab.net:65443/blueplanet/analytics (this repository)

## 0) required language
- Front-end: NodeJS<br>
- Back-end: NodeJS<br>
- Analysis: Python3.6+<br>

## 1) git clone each project
Go to favor directory on your computer
> $ git clone https://gitlab.mikelab.net:65443/blueplanet/fontend<br>
> $ git clone https://gitlab.mikelab.net:65443/blueplanet/backend<br>
> $ git clone https://gitlab.mikelab.net:65443/blueplanet/analytics<br>

## 2) back-end (both on local and production)
from parent directory
> $ cd backend/

install package using command `yarn` or `npm install`
> $ yarn

download `serviceKeyAccount.json` and `.env` via [link](https://drive.google.com/drive/folders/1DeOhtd_30hqlwL3_cbPWbZNQRmR2YL61?usp=sharing) using .ku.th account and paste them on the parent directory.

start server
> $ nodemon server.js


## 3) front-end 
from parent directory
> $ cd fontend/

install package using command `yarn` or `npm install`
> $ yarn

start server if on local use
> $ yarn start

but on production your have to add a env
> $ export REACT_APP_BACKEND_URL=mars.mikelab.net:30010<br>
and then start on production
> $ yarn start:production

## 4) analytics
from parent directory
> $ cd analytics/

install required package (pip version must >10.0.0)
> $ pip install --upgrade pip<br>
> $ pip install -r package_requirements.txt<br>
> $ pip install pythainlp<br>

upload the initial data via mongo console so you need to run mongo server and go to `mongo console` and run command 
> load("/path/to/parent/directory/mongo_js/initialize/[filename].js")

Moreover, these data files can be downloaded from [drive link](https://drive.google.com/drive/folders/1wHOqqVrMW1-9_kh0LXwvUXUu_UTAbrsb?usp=sharing).

using `python` or `python3` commands for running files, for example
> $ python3 [filename.py]

### directory and files explanation
#### 1. clicksteam/
contain `ranking.py` for ranking the top country by the number of threads which related to the country. The threads are considerd in each day (now it is not an automatic run) from each collection in `clicksteam` database.

#### 2. config/
config files of database and url

#### 3. utils/
contain lot of python files which provide lot of `necessary functions`

#### 4. naiveBayes-mmscale-interval-090320/ (one of the fail version)
- all steps from create text -> clean text -> TF-IDF -> Naive Bayes Classification -> prediction
- The `trained data` consist of only threads which `have only one theme`.
- In the TF-IDF step, it uses the `tf-idf` score for cutting words that have a low score.
- In Naive Bayes classification, there is only one model to predict multiple themes of each thread.
- But the results are unacceptable.
- contain `train.py` which the main file for execution

#### 5. nb-mmscale-interval-yesno-230320/ (the lastest version)
- all steps from create text -> clean text -> TF-IDF -> Naive Bayes Classification -> prediction results -> measurements.
- The `trained data` consist of only threads which `have only one theme`.
- In the TF-IDF step, it uses the `idf` score for cutting words that have a low score.
- In Naive Bayes classification, there are models of each theme and predict the theme to be yes or no. So, to create the model, trained threads(data) with one theme of the current considered theme will be 'yes' and others are 'no'. For example, the current consider theme is 'Mountain'. The threads with one theme and that theme is 'Mountain' will be the 'yes' class and The threads with one theme and that theme is not 'Mountain' will be the 'no' class. These are X_train and Y_train data.
- Using the Jaccard Similarity Index to measure the similarity between trained dataset and predicted dataset.
- contain `train.py` which the main file for execution
- contain many folders named `[theme]-idf-new` which keep model files.

#### 6. classification-accuracy.py
aim to calculate similarity of 304 threads between classify manually and classify by program. This file writes `checked_300threads.json` and `accuracy_300threads.json`.

#### 7. checked_300threads.json
the result of chacking and calculating similarity of 304 threads between classify manually and classify by program.

#### 8. accuracy_300threads.json
summary measurements of 304 threads which are classified manually.

#### 9. co-occurrenceTest.py
learn and try co-occurrence.

#### 10. countriesListSorted.json
A list contain all countries's information around the world which are sorted by country code.

#### 11. labeledThreadsbyHand_v2.csv
The data of threads are classified manually (by project's members).

#### 12. classificationByPattern.py
The main file of threads classification.

#### 13. scheduleClassify.py
is used to automatically call a classification function every day for data updating.
