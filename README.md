# YouTube Channel Recommender
This is a simple project that will recommend YouTube channels for you based on a search string.

Videos are queried by a search string and evaluated on the following criteria.

1. The description of the channel that hosts the videos is examined to see if it contains a term saimilar to the search string (relevance).
2. The comments on the video are examined to determine if the sentiment expressed inb them is positive.
3. The number of videos the channel has is considered.
4. The number of subscribers to the channel is considered.

The project is divided into frontend and backend code.

## Frontend
The frontend is implemented using Javascript and Vue. It runs in a docker container. The frontend implements the user interface only and relies on REST caslls
to the backend to access data.

```
cd frontend/youtube-scrapper
docker build -t youtube-scrapper-frontend .
docker run -p 5173:80 youtube-scrapper-frontend
```

## Backend
The backend code is written in python and uses Fast API to implement a REST endpoint. The backend also runs in a Docker container. The backend code uses the 
google-api-python-client package to query the YouTube data API and access information about YouTube videos. It uses the NLTK library to do sentiment analysis and 
fuzzy-wuzzy to determine relevance of a channel.

```
cd backend/src
docker build -t youtube-scrapper-backend --build-arg DEVELOPER_KEY=$DEVELOPER_KEY .
docker run -p 8000:8000 youtube-scrapper-backend
```

