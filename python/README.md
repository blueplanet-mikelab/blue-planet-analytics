# Blueplanet project installation
This project consist of 3 repositories
1. Front-end: https://gitlab.mikelab.net:65443/blueplanet/fontend
2. Back-end: https://gitlab.mikelab.net:65443/blueplanet/backend
3. Analytic: https://gitlab.mikelab.net:65443/blueplanet/analytics (this repository)

## 0) require language
Front-end: NodeJS
Back-end: NodeJS
Analysis: Python3.6+

## 1) git clone each project
Go to favor directory on your computer
> git clone https://gitlab.mikelab.net:65443/blueplanet/fontend
> git clone https://gitlab.mikelab.net:65443/blueplanet/backend
> git clone https://gitlab.mikelab.net:65443/blueplanet/analytics

## 2) back-end (both on local and production)
from parent directory
> cd backend/

install package using command `yarn` or `npm install`
> yarn

create `.env` on parent directory
> PORT="30010"
> MONGODB_URI="blueplanet:%40EmaiEkwai14@mars.mikelab.net:27017/blueplanet_project"
> MONGODB_THREADS_COLLECTION="classified_thread_20200425"
> MONGODB_MAP_COLLECTION="countries_list"
> MONGODB_TRIPLISTS_COLLECTION="triplists"
> MONGODB_FAVORITES_COLLECTION="favorites"
> MONGODB_RECENTLY_VIEWED_COLLECTION="recently_viewed"

start server
> nodemon server.js


## 3) front-end 
from parent directory
> cd fontend/

install package using command `yarn` or `npm install`
> yarn

start server if on local use
> yarn start

but on production your have to add a env
> export REACT_APP_BACKEND_URL=mars.mikelab.net:30010
and then start on production
> yarn start:production

## 4) analytics
from parent directory
> cd analytics/

install required package
> pip install -r package_requirements.txt



