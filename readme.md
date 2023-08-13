# Spotify Playlist Sorter
[![wakatime](https://wakatime.com/badge/user/aa966dfd-2ee1-42d6-8b74-530c65d62ac0/project/06685a36-b494-471d-8e5d-22fa20d885b7.svg)](https://wakatime.com/badge/user/aa966dfd-2ee1-42d6-8b74-530c65d62ac0/project/06685a36-b494-471d-8e5d-22fa20d885b7)

## About The Project
This playlist sorter was a project during Easter 2023 to experiment with the idea of how you sort a playlist. From working with the Spotify Web API during my A-Level project in 2021/22, I knew that Spotify categorised each track using different "audio features". These are float values between 0 and 1, and are created by analysisng the waveform, ect of the tracks. You can learn more about it [here](https://developer.spotify.com/documentation/web-api/reference/get-audio-features). 

In my A-Level project, I used these values to help predict the genre of a song, but I wanted to use them to see if I could make a playlist slowly flow between genres, to make the listening experience as nice as possible. The program slowly rebuilds the playlist, using the audio features and finding each tracks closest match. Although not perfect, it mostly seperates songs out by genre, and proved an interesting concept to explore!

## Technical Information
![Python](https://img.shields.io/badge/python-3670A0?style=flat-squared&logo=python&logoColor=ffdd54) 
Written for Python 3.10!

![Spotify](https://img.shields.io/badge/Spotify-1ED760?style=flat-squared&logo=spotify&logoColor=white)
Authenticates users using the [Authorization Code Flow](https://developer.spotify.com/documentation/web-api/tutorials/code-flow) and communicates with several API endpoints.

### Packages
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat-squared&logo=flask&logoColor=white)
Used to write the user interface, alongside 4 HTML templates.

![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=flat-squared&logo=pandas&logoColor=white)
Used for easier manipulation of the Spotify audio features.

